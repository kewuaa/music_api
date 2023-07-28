import asyncio
import json
import re
from functools import partial
from hashlib import md5
from typing import Optional

import aiohttp

from .._template import Template
from ..utils import get_time_stamp

kg_mid =  'ade3746ed936b2ae453020750b81844f'
kg_dfid =  '0R7uJo1fXgP43wvGER4dHu2X'
key = "NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt"


class API(Template):
    """ kugou music."""

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional
        """

        super().__init__(loop)
        self._compile = re.compile(r'{.*}')
        self._appid = self._loop.create_task(self._fetch_appid())

    async def _init_sess(self) -> aiohttp.ClientSession:
        """ initialize session.

        :return: ClientSession
        """

        return aiohttp.ClientSession(
            loop=self._loop,
            headers={
                "user-agent": await self.load_agents(),
            },
            cookies={
                'kg_mid': kg_mid,
                'kg_dfid': kg_dfid,
                'kg_dfid_collect': 'd41d8cd98f00b204e9800998ecf8427e',
            }
        )

    async def _fetch_appid(self) -> str:
        """ fetch kugou appid.

        :return: kugou appid
        """

        sess = await self._sess
        url = "https://www.kugou.com/"
        res = await sess.get(url)
        page = await res.text()
        appid = re.search(r"appid=(\d*)", page)
        if appid is None:
            raise RuntimeError("fetch kugou appid failed")
        return appid.group(1)

    async def search(self, keyword: str) -> list[Template.Song]:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(item) -> Template.Song:
            song_name = item['SongName']
            singer_name = item['SingerName']
            album_name = item['AlbumName']
            encode_album_audio_id = item["EMixSongID"]
            desc = [song_name, singer_name]
            if album_name:
                    desc.append(album_name)
            return Template.Song(
                desc=" -> ".join(desc),
                img_url=item["Image"],
                fetch=partial(self._fetch_song, encode_album_audio_id),
                owner=self,
            )
        sess = await self._sess
        appid = await self._appid
        url = "https://complexsearch.kugou.com/v2/search/song"
        params = {
            'callback': 'callback123',
            'keyword': keyword,
            'page': '1',
            'pagesize': '15',
            'bitrate': '0',
            'isfuzzy': '0',
            'inputtype': '0',
            'platform': 'WebFilter',
            'userid': '0',
            'clientver': '1000',
            'iscorrection': '1',
            'privilege_filter': '0',
            'filter': '10',
            'token': '',
            'srcappid': '2919',
            'clienttime': get_time_stamp(13),
            'mid': kg_mid,
            'uuid': kg_mid,
            'dfid': kg_dfid,
            'appid': appid,
        }
        key_str = key + "".join(f'{k}={params[k]}' for k in sorted(params)) + key
        params["signature"] = md5(key_str.encode()).hexdigest()
        res = await sess.get(url, params=params)
        res = await res.text()
        res = self._compile.findall(res)
        assert res
        res = json.loads(res[0])
        if res["error_code"] != 0:
            raise RuntimeError(f"search songs by keyword failed: {res['error_msg']}")
        return [parse(item) for item in res["data"]["lists"]]

    async def _fetch_song(self, id: str) -> tuple[Template.Song.Status, str]:
        """ fetch song.

        :param id: id of the song
        :return: fetch status and the url of the song
        """

        sess = await self._sess
        appid = await self._appid
        url = "https://wwwapi.kugou.com/yy/index.php"
        params = {
            "r": "play/getdata",
            "callback": "jQuery19109878419538462608_1688720900159",
            "dfid": kg_dfid,
            "appid": appid,
            "mid": kg_mid,
            "platid": "4",
            "encode_album_audio_id": id,
            "_": get_time_stamp(13),
        }
        res = await sess.get(url, params=params)
        res = await res.text()
        res = self._compile.findall(res)
        assert res
        res = json.loads(res[0])
        if res["err_code"] != 0:
            raise RuntimeError("fetch song failed")
        return Template.Song.Status.Success, res["data"]["play_url"]
