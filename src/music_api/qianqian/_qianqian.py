import asyncio
from typing import Optional
from hashlib import md5

from lxml.html import fromstring

from .._template import Template
from ..utils import get_time_stamp
appid = "16073360"
secret = "0b50b02fd0d73a9c4c8c3a781c30845f"


class API(Template):
    """ qianqian music."""

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional
        """

        super().__init__(loop)
        self.login = self.LoginHandleT(
            PWD=(None, self._login_by_pwd),
        )

    def _encrypt(self, params: dict) -> str:
        """ encrypt parameters and get parameter sign.

        :param params: parameters to encrypt
        :return: encrypted string
        """

        s = '&'.join(f'{key}={params[key]}'for key in sorted(params)) + secret
        return md5(s.encode()).hexdigest()

    async def search(self, keyword: str) -> list[Template.SongInfo]:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(tree) -> Template.SongInfo:
            return Template.SongInfo(
                desc=" -> ".join(tree.xpath(".//a/text()")),
                id=(tree.xpath(".//a/@href")[0].split("/")[-1],),
                master=self,
            )
        sess = await self._sess
        url = "https://music.91q.com/search"
        params = {
            "word": keyword,
        }
        res = await sess.get(url, params=params)
        page = await res.text()
        tree = fromstring(page)
        items = tree.xpath('//li[@class="pr t clearfix"]')
        return [parse(item) for item in items]

    async def fetch_song(self, info: Template.SongInfo) -> Template.Song:
        """ fetch song by SongInfo.

        :param info: SongInfo
        :return: Song object
        """

        sess = await self._sess
        url = "https://music.91q.com/v1/song/tracklink"
        params = {
            "appid": appid,
            "TSID": info.id[0],
            "timestamp": get_time_stamp(),
        }
        params["sign"] = self._encrypt(params)
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if res["errno"] != 22000:
            raise RuntimeError(f"fetch song failed: {res['errmsg']}")
        info.img_url = res["data"]["pic"]
        if res["data"]["isVip"]:
            return Template.Song(status=Template.Song.Status.NeedVIP)
        return Template.Song(url=res["data"]["path"], format=res["data"]["format"])

    async def _login_by_pwd(self, login_id: str, password: str, _) -> None:
        """ log in by id and password.

        :param login_id: log in id
        :param password: password
        """

        sess = await self._sess
        url = "https://music.91q.com/v1/oauth/login/password"
        time_stamp = get_time_stamp()
        data = {
            'phone': login_id,
            'password': md5(password.encode()).hexdigest(),
            'appid': appid,
            'timestamp': time_stamp,
        }
        params = {
            "sign": self._encrypt(data),
            "timestamp": time_stamp,
        }
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["errno"] != 22000:
            raise RuntimeError(f"log in by pwd failed: {res['errmsg']}")
        token = res["data"]["access_token"]
        sess.cookie_jar.update_cookies({
            "token_type": "access_token",
            "access_token": token,
            "refresh_token": token,
        })
