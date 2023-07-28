import asyncio
from functools import partial
from hashlib import md5
from typing import Optional

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

        self.login = self.LoginHandleT(
            PWD=(None, self._login_by_pwd),
        )
        super().__init__(loop)

    def _encrypt(self, params: dict) -> str:
        """ encrypt parameters and get parameter sign.

        :param params: parameters to encrypt
        :return: encrypted string
        """

        s = '&'.join(f'{key}={params[key]}'for key in sorted(params)) + secret
        return md5(s.encode()).hexdigest()

    async def search(self, keyword: str) -> list[Template.Song]:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(tree) -> Template.Song:
            id = tree.xpath(".//a/@href")[0].split("/")[-1]
            return Template.Song(
                desc=" -> ".join(tree.xpath(".//a/text()")),
                fetch=partial(self._fetch_song, id),
                owner=self,
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

    async def _fetch_song(self, id: str) -> tuple[Template.Song.Status, str]:
        """ fetch song.

        :param id: id of the song
        :return: fetch status and the url of the song
        """

        sess = await self._sess
        url = "https://music.91q.com/v1/song/tracklink"
        params = {
            "appid": appid,
            "TSID": id,
            "timestamp": get_time_stamp(),
        }
        params["sign"] = self._encrypt(params)
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if res["errno"] != 22000:
            raise RuntimeError(f"fetch song failed: {res['errmsg']}")
        # img_url = res["data"]["pic"]
        # format = res["data"]["format"]
        if res["data"]["isVip"]:
            return Template.Song.Status.NeedVIP, ""
        return Template.Song.Status.Success, res["data"]["path"]

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
