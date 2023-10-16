import asyncio
import base64
import json
import math
from ctypes import c_uint32
from functools import partial
from pathlib import Path
from secrets import randbelow
from time import time
from typing import Optional

import aiohttp

from .._template import Template

MAX_INT = 2 ** 31
jscsript_path = Path(__file__).parent / "encrypt.js"


def int_overflow(val: int) -> int:
    if not -MAX_INT <= val <= MAX_INT - 1:
        val = (val + MAX_INT) % (2 * MAX_INT) - MAX_INT
    return val


def unsigned_right_shitf(n, i):
    # 数字小于0，则转为32位无符号uint
    if n < 0:
        n = c_uint32(n).value
    # 正常位移位数是为正数，但是为了兼容js之类的，负数就右移变成左移好了
    if i < 0:
        return -int_overflow(n << abs(i))
    # print(n)
    return int_overflow(n >> i)


def reqid():
    r = None
    o = None
    d = 0

    def get_reqid():
        nonlocal r, o, d
        b = []
        f = r
        v = o
        if f is None or v is None:
            m = [randbelow(256) for _ in range(16)]
            r = f = f or [1 | m[0], m[1], m[2], m[3], m[4], m[5]]
            o = v = v or 16383 & (int_overflow(m[6] << 8) | 7)
        y = int(time() * 1000)
        w = d + 1
        d = w
        x = (10000 * (268435455 & (y := y + 12219292800000)) + w) % 4294967296
        b.append(unsigned_right_shitf(x, 24) & 255)
        b.append(unsigned_right_shitf(x, 16) & 255)
        b.append(unsigned_right_shitf(x, 8) & 255)
        b.append(255 & x)
        _x = int(y / 4294967296 * 10000) & 268435455
        b.append(unsigned_right_shitf(_x, 8) & 255)
        b.append(255 & _x)
        b.append(unsigned_right_shitf(_x, 24) & 15 | 16)
        b.append(unsigned_right_shitf(_x, 16) & 255)
        b.append(unsigned_right_shitf(v, 8) | 128)
        b.append(255 & v)
        b.extend(f)
        result = [f'{hex(i)[2:]:0>2}' for i in b]
        result.insert(10, '-')
        result.insert(8, '-')
        result.insert(6, '-')
        result.insert(4, '-')
        return ''.join(result)
    return get_reqid


def encrypt(value: str, cookie_key: str) -> str:
    # key = "".join(str(ord(s)) for s in cookie_key)
    # key = (
    #     "7210995731171181169599100985350521025250102489910149579849545798564855"
    #     "504950519752555055"
    # )
    o = 91455
    l = 22
    # c = 2 ** 31 - 1
    c = 2147483647
    # d = int(round(1e9 * random()) % 1e8)
    d = 30061716
    key = 1103782257
    f = ""
    for s in value:
        h = ord(s) ^ math.floor(key / c * 255)
        if h < 16:
            f += f"0{hex(h)[2:]}"
        else:
            f += str(hex(h)[2:])
        key = (o * int(key) + l) % c
    # d = f"{hex(d)[2:]:0>8}"
    d = "01cab494"
    return f + d


class API(Template):
    """ kuwo music."""

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional
        """

        self.login = self.LoginHandleT(
            PWD=(self._fetch_captcha, self._login_by_pwd),
            SMS=(self._fetch_captcha, self._send_sms, self._login_by_sms)
        )
        super().__init__(loop)
        self._gen_reqid = reqid()
        self._captcha = ""
        self._captcha_token = ""
        self._sms_tm = 0

    async def _init_sess(self) -> aiohttp.ClientSession:
        """ initialize session.

        :return: ClientSession
        """

        sess = aiohttp.ClientSession(
            loop=self._loop,
            headers={
                "Content-Type": "application/json;charset=utf-8",
                "user-agent": await self.load_agents(),
                "Referer": "https://www.kuwo.cn/",
                "Host": "www.kuwo.cn",
            },
            # cookies={"Hm_token": "chB5p2Fz5DyxewBQ7Qm8PH7j4Y44JnrS"}
        )
        await sess.get("http://www.kuwo.cn/")
        return sess

    async def _session(self) -> aiohttp.ClientSession:
        """ get ClientSession and update csrf in headers.

        :return: ClientSession
        """

        sess = await self._sess
        cookies = sess.cookie_jar.filter_cookies("https://www.kuwo.cn/") # pyright: ignore
        token = cookies.get("Hm_Iuvt_cdb524f42f0cer9b268e4v7y735ewrq2324")
        assert token is not None
        token = token.value
        # proc = await asyncio.create_subprocess_shell(
        #     f"node {jscsript_path} {token} Hm_Iuvt_cdb524f42f0ce19b169b8072123a4727",
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE,
        # )
        # stdout, stderr = await proc.communicate()
        # if stderr:
        #     raise RuntimeError(f"execute js script failed: {stderr.decode()}")
        # sess.headers["Secret"] = stdout.decode().strip()
        sess.headers["Secret"] = encrypt(
            token,
            "Hm_Iuvt_cdb524f42f0cer9b268e4v7y735ewrq2324"
        )
        return sess

    async def search(self, keyword: str) -> list[Template.Song]:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(item: dict) -> Template.Song:
            return Template.Song(
                    desc=" -> ".join((item["NAME"], item["ARTIST"], item["ALBUM"])),
                    img_url="https://img2.kuwo.cn/star/albumcover/" + item["web_albumpic_short"],
                    fetch=partial(self._fetch_song, item["DC_TARGETID"]),
                    owner=self,
                )
        sess = await self._session()
        url = "https://www.kuwo.cn/search/searchMusicBykeyWord"
        params = {
            "vipver": "1",
            "client": "kt",
            "ft": "music",
            "cluster": "0",
            "strategy": "2012",
            "encoding": "utf8",
            "rformat": "json",
            "mobi": "1",
            "issubtitle": "1",
            "show_copyright_off": "1",
            "pn": "0",
            "rn": "20",
            "all": keyword,
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        items = res["abslist"]
        return [parse(item) for item in items]

    async def _fetch_song(self, id: str) -> tuple[Template.Song.Status, str]:
        """ fetch song.

        :param id: id of the song
        :return: fetch status and the url of the song
        """

        sess = await self._session()
        url = "https://www.kuwo.cn/api/v1/www/music/playUrl"
        params = {
            "mid": id,
            "type": "music",
            "httpsStatus": "1",
            "reqId": self._gen_reqid(),
            "plat": "web_www",
            "from": "",
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if not res["success"]:
            if res.get("code") == -1:
                return Template.Song.Status.NeedVIP, ""
            raise RuntimeError(f"fetch song failed: {res['message']}")
        return Template.Song.Status.Success, res["data"]["url"]

    async def _fetch_captcha(self) -> bytes:
        """ fetch captcha.

        :return: captcha bytes
        """

        sess = await self._session()
        url = "http://www.kuwo.cn/api/common/captcha/getcode"
        params = {
            "reqId": self._gen_reqid(),
            "httpsStatus": "1",
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"fetch captcha failed: {res['msg']}")
        captcha: str = res["data"]["img"]
        self._captcha_token = res["data"]["token"]
        self._captcha = captcha
        prefix = "data:image/jpeg;base64,"
        assert captcha.startswith(prefix)
        return base64.b64decode(captcha[len(prefix):].encode())

    async def _login_by_pwd(self, login_id: str, password: str, captcha: str) -> None:
        """ log in by id and password.

        :param login_id: log in id
        :param password: password
        :param captcha: captcha
        """

        sess = await self._session()
        url = "https://wapi.kuwo.cn/api/www/login/loginByKw"
        params = {
            "reqId": self._gen_reqid(),
            "httpsStatus": "1",
        }
        data = {
            'userIp': 'www.kuwo.cn',
            'uname': login_id,
            'password': password,
            'verifyCode': captcha,
            'img': self._captcha,
            'verifyCodeToken': self._captcha_token,
        }
        res = await sess.post(url, data=json.dumps(data), params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"log in by pwd failed: {res['msg']}")
        cookies = res["data"]["cookies"]
        sess.cookie_jar.update_cookies(cookies)

    async def _send_sms(self, cellphone: str, captcha: str) -> None:
        """ send sms.

        :param cellphone: phone number
        :param captcha: captcha
        """

        sess = await self._session()
        url = "https://kuwo.cn/api/sms/mobileLoginCode"
        params = {
            "reqId": self._gen_reqid(),
            "httpsStatus": "1",
        }
        data = {
            "mobile": cellphone,
            "userIp": "www.kuwo.cn",
            "verifyCode": captcha,
            "verifyCodeToken": self._captcha_token,
        }
        res = await sess.post(url, data=json.dumps(data), params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"send sms failed: {res['msg']}")
        self._sms_tm = res["data"]["tm"]

    async def _login_by_sms(
        self,
        cellphone: str,
        verify_code: str,
        captcha: str
    ) -> None:
        """ log in by sms.

        :param cellphone: phone number
        :param verify_code: verify code
        :param captcha: captcha need by sending sms
        """

        sess = await self._session()
        url = "https://wapi.kuwo.cn/api/www/login/loginByMobile"
        params = {
            "reqId": self._gen_reqid(),
            "httpsStatus": "1",
        }
        data = {
            "mobile": cellphone,
            "smsCode": verify_code,
            "tm": self._sms_tm,
            "verifyCode": captcha,
        }
        res = await sess.post(url, data=json.dumps(data), params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"log in by sms failed: {res['msg']}")
        cookies = res["data"]["cookies"]
        sess.cookie_jar.update_cookies(cookies)
