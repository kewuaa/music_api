import asyncio
import base64
import json
from hashlib import md5
from http.cookies import SimpleCookie
from io import BytesIO
from typing import Awaitable, Callable, Optional

from qrcode import make as make_qrcode

from .._template import Template
from ..lib.AES import AES
encSecKey = (
    "21e8dcd7b013c2e56af244ad4e55484d5840b108df255fbeccf88e8187362476af2cc881a6"
    "1884aea955937337fe3bdfe896a62c27606da8aea2f3c93b9bb6c6e0c17b85da6e3a766d58"
    "0286967975db7f0f38ef88d582b39f92058deff794b705702e70be6f26b93c206e55e55e6a"
    "51874469fd11cdff86df742c3b9dd89abe"
)
i = 'jkUEeutwbd2HLFNL'
g = '0CoJUm6Qyw8W8jud'



class API(Template):
    """ wangyiyun music."""

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional
        """

        super().__init__(loop)
        self.login = self.LoginHandleT(
            QR=self._login_by_qrcode,
            # PWD=(None, self._login_by_pwd),
            # SMS=(None, self._send_sms, self._login_by_sms),
        )
        self._csrf_token = ""

    def _aes(self, s: str, key: str) -> str:
        """ aes encrypt.

        :param s: string to encrypt
        :param key: aes key
        :return: encrypted string
        """

        s = s.encode()
        pad = 16 - len(s) % 16
        s += chr(pad).encode() * pad
        aes = AES.new(key.encode(), AES.MODE_CBC, b'0102030405060708')
        return base64.b64encode(aes.encrypt(s)).decode()

    def _encrypt(self, data: dict) -> str:
        """ encrypt data.

        :param data: data to post
        :return: encrypted string
        """

        s = json.dumps(data)
        s = self._aes(s, g)
        s = self._aes(s, i)
        return {
            "params": s,
            "encSecKey": encSecKey,
        }

    async def _fetch_unikey(self) -> str:
        """ fetch unikey needed by fetching qr code."""

        sess = await self._sess
        url = "https://music.163.com/weapi/login/qrcode/unikey"
        params = {
            "csrf_token": self._csrf_token,
        }
        data = {
            'type': 1,
            'noCheckToken': 'true',
            "csrf_token": self._csrf_token,
        }
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError("fetch unikey failed")
        return res["unikey"]

    async def search(self, keyword: str) -> Template.SongInfo:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(item: dict) -> Template.SongInfo:
            return Template.SongInfo(
                desc=" -> ".join((
                    item["name"],
                    "/".join(ar["name"] for ar in item["ar"]),
                    item["al"]["name"],
                )),
                img_url=item["al"]["picUrl"],
                id=(item["id"],),
                master=self,
            )
        sess = await self._sess
        url = "https://music.163.com/weapi/cloudsearch/get/web"
        params = {
            "csrf_token": self._csrf_token,
        }
        data = {
            "hlpretag": "<span class=\"s-fc7\">",
            "hlposttag": "</span>",
            "s": keyword,
            "type": '1',
            "offset": '0',
            "total": "true",
            "limit": "30",
            "csrf_token": self._csrf_token,
        }
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError("search song by keyword failed")
        return [parse(item) for item in res["result"]["songs"]]

    async def fetch_song(self, info: Template.SongInfo) -> Template.Song:
        """ fetch song by SongInfo.

        :param info: SongInfo
        :return: Song object
        """

        sess = await self._sess
        url = "https://music.163.com/weapi/song/enhance/player/url/v1"
        params = {
            "csrf_token": self._csrf_token
        }
        data = {
            'ids': f'[{info.id[0]}]',
            'level': 'standard',
            'encodeType': 'aac',
            'csrf_token': self._csrf_token,
        }
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError("fetch song failed")
        song_url = res["data"][0]["url"]
        if song_url is None:
            return Template.Song(status=Template.Song.Status.NeedVIP)
        return Template.Song(url=song_url, format=res["data"][0]["type"])

    async def _update_token(self) -> None:
        """ update csrf_token after log in."""

        sess = await self._sess
        cookies: SimpleCookie = sess.cookie_jar.filter_cookies("https://music.163.com/")
        csrf_token = cookies.get("__csrf")
        self._csrf_token = "" if csrf_token is None else csrf_token.value

    async def _fetch_qrcode(self) -> tuple[bytes, str]:
        """ fetch qr code to log in.

        :return: qr code bytes and qr code unikey
        """

        unikey = await self._fetch_unikey()
        url = "http://music.163.com/login?codekey=" + unikey
        qc = make_qrcode(url)
        f = BytesIO()
        qc.save(f)
        return f.getvalue(), unikey

    async def _login_by_qrcode(
        self,
        qrcode_handle: Callable[[bytes], Awaitable[None]]
    ) -> None:
        """ log in by qr code.

        :param qrcode_handle: handle to show qr code
        """

        sess = await self._sess
        qrcode, unikey = await self._fetch_qrcode()
        task = self._loop.create_task(qrcode_handle(qrcode))
        qrcquery_url = "https://music.163.com/weapi/login/qrcode/client/login"
        params = {
            "csrf_token": self._csrf_token,
        }
        data = {
            "type": 1,
            "noCheckToken": "true",
            "key": unikey,
            "csrf_token": self._csrf_token,
        }
        data = self._encrypt(data)
        while 1:
            res = await sess.post(qrcquery_url, data=data, params=params)
            res = await res.json(content_type=None)
            status_code = res["code"]
            # 803 -> successfully log in
            # 800 -> qr code timeout
            # 802 -> scanned and need to ensure on phone
            # 801 -> wait for scanning
            if status_code == 803:
                await self._update_token()
                account_url = "https://music.163.com/weapi/w/nuser/account/get"
                res = await sess.post(
                    account_url,
                    data=self._encrypt({"csrf_token": self._csrf_token}),
                    params={"csrf_token": self._csrf_token},
                )
                res = await res.json(content_type=None)
                break
            elif status_code in (800, 801, 802):
                if status_code == 800:
                    task.cancel()
                    await self._login_by_qrcode(qrcode_handle)
                    break
            else:
                raise RuntimeError(
                    f"log in by qr code failed: {res['message']}"
                )
            await asyncio.sleep(1)

    async def _login_by_pwd(self, login_id: str, password: str, _) -> None:
        """ log in by id and password.

        :param login_id: log in id
        :param password: password
        """

        sess = await self._sess
        password = md5(password.encode()).hexdigest()
        params = {
            "csrf_token": self._csrf_token,
        }
        if '@' in login_id:
            data = {
                'username': login_id,
                'password': password,
                'rememberLogin': 'true',
                'clientToken': '1_jVUMqWEPke0/1/Vu56xCmJpo5vP1grjn_SOVVDzOc78w'
                '8OKLVZ2JH7IfkjSXqgfmh',
            }
            url = 'http://music.163.com/weapi/login'
        else:
            data = {
                'phone': login_id,
                'password': password,
                'rememberLogin': 'true',
            }
            url = 'https://music.163.com/weapi/login/cellphone'
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"log in by pwd failed: {res['message']}")
        await self._update_token()

    async def _send_sms(self, cellphone: str, _) -> None:
        """ send sms.

        :param cellphone: phone number
        """

        sess = await self._sess
        url = "http://music.163.com/weapi/sms/captcha/sent"
        params = {
            "csrf_token": self._csrf_token,
        }
        data = {
            "cellphone": cellphone,
            "ctcode": 86,
        }
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError("send sms failed")

    async def _login_by_sms(self, cellphone: str, verify_code: str, _) -> None:
        """ log in by sms.

        :param cellphone: phone number
        :param verify_code: verify code
        """

        sess = await self._sess
        url = "http://music.163.com/weapi/sms/captcha/verify"
        params = {
            "csrf_token": self._csrf_token,
        }
        data = {
            "cellphone": cellphone,
            "captcha": verify_code,
            "ctcode": 86,
            "csrf_token": self._csrf_token,
        }
        data = self._encrypt(data)
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["code"] != 200:
            raise RuntimeError(f"log in by sms failed: {res['message']}")
        print(self._csrf_token)
        await self._update_token()
        print(self._csrf_token)
