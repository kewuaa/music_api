import json
import base64
import asyncio
from typing import Optional, Awaitable, Callable
from urllib.parse import quote
from hashlib import sha1
from re import compile

import aiohttp
from lxml.html import fromstring

from .._template import Template
from ..lib.RSA import RSA
from ..lib.AES import encrypt
from ..utils import get_time_stamp
cookie_id = "8ad12619-c027-452a-b229-70bb4efb4637-n41688289353375"
fingerPrint = (
    "365f397d7a702e0ba61a0c81be7447500c0568561479bcb3da6ba896070cc336f6e8e3d505"
    "1a38a243ac8cfc57c642c897e04785ab7e2fbc9c674322cd697a3e70389cf3b5ae23e11729"
    "4f895975aece81c93854dd97025f55cab44a5ef54a35cc0561354a8755a35d0ba0d625b8fa"
    "b4c4cd8581009ae0c9570fb29ee715fed3"
)
fingerPrintDetail = (
    "1f33883710fa9e30f6ecdb2324fcfea43a542590751fc54a08f094ceb440f5d680327edbf7"
    "09f48390419d796628e32d5d8c44d4e79d6087d3963c71b260033023de27504d17d1e4c7fb"
    "925ee5ce4224569c5073e050462947781d2c57f551480ff194984fda31651a82c75d12cd72"
    "776f950a9aea82c8e5bc03744929f53864644ea8109ffdf2284db2a7799537ff50f8c0b9f1"
    "60ddf45582a12c4fd500cd07c6d4eded3120f73ba57e5cb59986463c992d1ffe89df8307be"
    "6bd532a5842bedcaaf9138b905e28bc9f2e9a17e58a6e2f954e46f48cb5a86a77470c11c35"
    "20213879df9da08e243c5a1ab96d809b272d9c47682a5297eed2c6efff7dc4c04279690977"
    "1a6baa300b7bb652901be5a399f6a5193ba54fcf1e9d227431539df077b1b97afe235007fd"
    "777b4e21b22bdfb231190747296d704d0070e5e818195f50f81734a7b34376fc314ec14a35"
    "30830354f1b261112c21ac9f53be126b6a5e68b9568e584fed59a71c7c859c7be6a4cf4464"
    "942bd9abf6efb8ca1922140204051621c2588c7a7824996401a2fc40a1416683e40874fa61"
    "72471146329c19db6ee497a0134d415189d8d67e9e41b8a0ab7d1de8547de01e824fb64e72"
    "acb13a4d954177bddac21ec5b0442c12e501cb42c50904aaec011e36b283b046a6d57576f9"
    "069940c4d6cfe51ddbd88e0e5628b25a954e2a57a3cdaedede781724b2f6d551ae34933c11"
    "033b1dffa5bc9cc5d52e6b1eb07ad85968298c0a87264c0d174dea088ae3cff2f79c9ab80e"
    "6b508d1bb25175195387715b9c87a2e5d0267ef85f2fdc5d845a21f800453da1b826ad588f"
    "b8eaa3927f8f9fde13f4994f8a4d83743ce2cbf766b3785cce8b7e33d75b77e4d54d1c0d1b"
    "aeb3dcf342911d5224e60b2ee90423bd9b190fd458c875c7caae6a6a3111bea15800114d27"
    "5bf3105551784a4d438ad57f8b2a5e4cf2ffb13420e5fa806df5c6b4ed8aab82fceabd5dc3"
    "8e887ff327d2c0afa2d7847c2478a4c80b422ea6da5aef564046da772f24a943c7f171cdd5"
    "6188b9bc7b105762a45a1fc5478a02a1d338bed5b084e7c72195a37c41aeb4b171437a464d"
    "94b5f099b3987aa91e5af685fe9605ea51d362b05596ca55243ff5884c75742f2a21d0b252"
    "34cc1dd08192569167d14a27af4634b51122722250d05d0010c00ca04c053959a3bf8327a3"
    "c21398ff4a54ab002ee83e4e4b010f12152c32136c1a093a16da2dba1fe4d45b3a634cf34a"
    "72a976635516bce37904cff9621c93a2e0641e5ef1c6d76c6c48c323732c32dfde0dcbc6ab"
    "ed4261d0d3e1072dc5468487711df62cc79bfcc08579c9e25d7fb0ce176d2ef8ad69f38c2a"
    "180cc5b5963c89be7c64732caf5e328a5705641033c7b3921d03da10f99e97b5b8ae7bb6f6"
    "a9f664fe67ec37207aba8167f170cdb8d4fe532160cf8e86ad21379ff701340bfe1025c996"
    "c67067572a1965e18811dfc305757441201f5f2324cff51c0da67cf767301fb3290a7f7fda"
    "ad1e0573ae5373bbb3ecaa5e11f825f984f46ffb2bcf315bb786aa44697ef4b48257402ac9"
    "a6422ecb461838dabaa2064d4bca296b98a75126eea5971120aa392c4e32bd9a8d3e4b8ca8"
    "989b11d0d1"
)


class API(Template):
    """ migu music."""

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional
        """

        self.login = self.LoginHandleT(
            QR=self._login_by_qrcode,
            PWD=(self._fetch_captcha, self._login_by_pwd),
            SMS=(self._fetch_captcha, self._send_sms, self._login_by_sms),
        )
        super().__init__(loop)
        self._app_info: Awaitable[dict] = \
            self._loop.create_task(self._init_migu_app())
        self._publickey: Awaitable[RSA]  = \
            self._loop.create_task(self._fetch_publickey())

    async def _init_sess(self) -> aiohttp.ClientSession:
        """ initialize session.

        :return: ClientSession
        """

        return aiohttp.ClientSession(
            loop=self._loop,
            headers={
                "user-agent": await self.load_agents(),
                'Referer': 'https://music.migu.cn/v3',
            },
            cookies={"migu_cookie_id": cookie_id}
        )

    async def _init_migu_app(self) -> dict:
        """ initialize migu app.

        :return: migu app information
        """

        sess = await self._sess
        url = "https://music.migu.cn/v3"
        res = await sess.get(url)
        page = await res.text()
        info = compile("var MUSIC_CONFIG.*?{([\S\s]+?)}").\
            search(page).group(1)
        return {
            k.strip(): v.strip().strip("'").strip('"')
            for k, v in [
                pair.split(':', 1)
                for pair in info.split(',\n')
                if pair
            ]
        }

    async def _fetch_publickey(self) -> RSA:
        """ fetch the public key.

        :return: RSA object
        """

        sess = await self._sess
        url = "https://passport.migu.cn/password/publickey"
        res = await sess.post(url)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"fetch publickey failed: {res['message']}")
        publickey = res["result"]
        return RSA(publickey['modulus'], publickey['publicExponent'])

    async def _encrypt(self, params: dict) -> str:
        """ encrypt parameters and get parameter i.

        :param params: parameters to encrypt
        :return: encrypted string
        """

        sess = await self._sess
        params = params.copy()
        params['keyword'] = quote(params['keyword'])
        params['u'] = sess.headers['user-agent'] + '/' \
            + (await self._app_info)["SOURCE_ID"]
        params['k'] = cookie_id
        key_str = ''.join(k + str(params[k]) for k in sorted(params))
        key_str = quote(key_str, safe='()')
        return sha1(key_str.encode()).hexdigest()

    async def search(self, keyword: str) -> list[Template.SongInfo]:
        """ search song by keyword.

        :param keyword: keyword to search
        :return: list of search result
        """

        def parse(tree) -> Template.SongInfo:
            info = tree.xpath(
                './div[@class="song-actions single-column"]//@data-share',
            )[0]
            info_dict = json.loads(info)
            desc = [info_dict['title'], info_dict['singer']]
            if info_dict.get('album') is not None:
                desc.append(info_dict['album'])
            img_url = info_dict["imgUrl"]
            source_id = info_dict['linkUrl'].split('/')[-1]
            return Template.SongInfo(
                desc=" -> ".join(desc),
                img_url=img_url,
                id=(source_id,),
                master=self,
            )
        sess = await self._sess
        app_info = await self._app_info
        url = "https://music.migu.cn/v3/search"
        params = {
            "f": "html",
            "s": get_time_stamp(),
            "c": app_info["CHANNEL_ID"],
            "keyword": keyword,
            "v": app_info["APP_VERSION"],
        }
        i = await self._encrypt(params)
        params.update({
            "i": i,
            "page": 1,
            "type": "song",
        })
        res = await sess.get(url, params=params)
        page = await res.text()
        tree = fromstring(page)
        items = tree.xpath('//div[@class="songlist-body"]/div')
        return [parse(tree) for tree in items]

    async def fetch_song(self, info: Template.SongInfo) -> Template.Song:
        """ fetch song by SongInfo.

        :param info: SongInfo
        :return: Song object
        """

        sess = await self._sess
        url = "https://music.migu.cn/v3/api/music/audioPlayer/getPlayInfo"
        sess.headers["Referer"] = "https://music.migu.cn/v3/music/player/audio"
        key = \
            '4ea5c508a6566e76240543f8feb06fd457777be39549c4016436afda65d2330e'
        data = {
            'copyrightId': info.id[0],
            'type': 2,  # """ type: 标准:1 高品:2 无损:3,至臻:4 3D:5 """
            "auditionsFlag": 11,
        }
        data = json.dumps(data).replace(' ', '')
        data = encrypt(data, key).decode()
        params = {
            'dataType': 2,
            'data': data,
            'secKey':
            'kHJ2i6869DhR3vATP9q1bBGWyL4gPbSQDMUMM/pHQpWr721h4K6UnptCgioY23Xcc'
            'BjCWdQepKlOV55c8aEL9VM0M47PBqSgrqR/rksGCpY4VukRY5bZjBMXeV7l78eErH'
            '9c4wh5x2BG4Y7PiW15Xod2DTQIziD2IYDly+RSI9U='
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        status_code = res["returnCode"]
        if status_code != '000000':
            if status_code == 'N000000':
                # print(res["msg"])
                return Template.Song(
                    status=Template.Song.Status.NeedLogin
                )
            else:
                raise RuntimeError(f"fetch song failed: {res['msg']}")
        song_url = res['data']['playUrl']
        if song_url:
            return Template.Song(url="https:" + song_url)

    async def _fetch_captcha(self) -> bytes:
        """ fetch captcha.

        :return: captcha bytes
        """

        sess = await self._sess
        app_info = await self._app_info
        url = "https://passport.migu.cn/captcha/graph/risk"
        params = {
            'imgcodeType': 2,
            'showType': 1,
            'sourceid': app_info["SOURCE_ID"],
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"fetch sms verify code failed: {res['message']}")
        captcha: str = res["result"]["captchaurl"]
        prefix = "data:image/jpeg;base64,"
        assert captcha.startswith(prefix)
        return base64.b64decode(captcha[len(prefix):].encode())

    async def _check_captcha(self, captcha: str) -> None:
        """ check if captcha valid.

        :param captcha: captcha
        """

        sess = await self._sess
        app_info = await self._app_info
        url = "https://passport.migu.cn/captcha/graph/check"
        data = {
            'isAsync': 'true',
            'captcha': captcha,
            'imgcodeType': 2,
            'sourceid': app_info["SOURCE_ID"],
        }
        res = await sess.post(url, data=data)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"check verify code: {res['message']}")

    async def _verify_token(self, url: str, token: str, tp: str) -> None:
        """ verify the token so that the cookies could be updated.

        :param url: url to verify
        :param token: token to verify
        :param tp: log in type
        """

        sess = await self._sess
        params = {
            'callbackURL': 'https://music.migu.cn/v3',
            'relayState': '',
            'token': token,
            'qrclogin': 1,
            'logintype': tp,
        }
        res = await sess.get(url, params=params)
        if res.status != 200:
            raise RuntimeError(f"verify token failed, the logintype is {tp}")

    async def _fetch_qrcode(self) -> tuple[bytes, str]:
        """ fetch qr code to log in.

        :return: qr code bytes and qr code session id
        """

        sess = await self._sess
        url = "https://passport.migu.cn/api/qrcWeb/qrcLogin"
        app_info = await self._app_info
        params = {"sourceID": app_info["SOURCE_ID"]}
        data = {
            "isAsync": "true",
            "sourceid": app_info["SOURCE_ID"],
        }
        res = await sess.post(url, data=data, params=params)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"fetch qr code failed: {res['message']}")
        qrcode: str = res["result"]["qrcUrl"]
        prefix = "data:image/jpeg;base64,"
        assert qrcode.startswith(prefix)
        return (
            base64.b64decode(qrcode[len(prefix):].encode()),
            res["result"]["qrc_sessionid"],
        )

    async def _login_by_qrcode(
        self,
        qrcode_handle: Callable[bytes, Awaitable[None]]
    ) -> None:
        """ log in by qr code.

        :param qrcode_handle: handle to show qr code
        """

        sess = await self._sess
        app_info = await self._app_info
        qrcode, sessionid = await self._fetch_qrcode()
        task = self._loop.create_task(qrcode_handle(qrcode))
        qrcquery_url = "https://passport.migu.cn/api/qrcWeb/qrcquery"
        params = {
            "isAsync": "true",
            "sourceid": app_info["SOURCE_ID"],
            "qrc_sessionid": sessionid,
        }
        while 1:
            res = await sess.post(qrcquery_url, params=params)
            res = await res.json(content_type=None)
            status_code = res["status"]
            # 2000 -> successfully log in
            # 4072 -> qr code timeout
            # 4073 -> scanned and need to ensure on phone
            # 4074 -> wait for scanning
            if status_code == 2000:
                # print(res)
                await self._verify_token(
                    res["result"]["redirectURL"],
                    res["result"]["token"],
                    "QRCSSO",
                )
                break
            elif status_code in (4072, 4073, 4074):
                if status_code == 4072:
                    task.cancel()
                    await self._login_by_qrcode(qrcode_handle)
                    break
            else:
                raise RuntimeError(
                    f"log in by qr code failed: {res['message']}"
                )
            await asyncio.sleep(1)

    async def _login_by_pwd(self, login_id: str, password: str, captcha: str) -> None:
        """ log in by id and password.

        :param login_id: log in id
        :param password: password
        :param captcha: captcha
        """

        await self._check_captcha(captcha)
        sess = await self._sess
        app_info = await self._app_info
        publickey = await self._publickey
        url = "https://passport.migu.cn/authn"
        data = {
            'sourceID': app_info['SOURCE_ID'],
            'appType': 0,
            'relayState': '',
            'loginID': publickey.encrypt(login_id),
            'enpassword': publickey.encrypt(password),
            'captcha': captcha,
            'imgcodeType': 1,
            'rememberMeBox': 1,
            'fingerPrint': fingerPrint,
            'fingerPrintDetail': fingerPrintDetail,
            'isAsync': 'true',
        }
        res = await sess.post(url, data=data)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"log in by pwd failed: {res['message']}")
        await self._verify_token(
            res["result"]["redirectURL"],
            res["result"]["token"],
            "PWD",
        )

    async def _send_sms(self, cellphone: str, captcha: str) -> None:
        """ send sms.

        :param cellphone: phone number
        :param captcha: captcha
        """

        await self._check_captcha(captcha)
        sess = await self._sess
        app_info = await self._app_info
        publickey = await self._publickey
        url = "https://passport.migu.cn/login/dynamicpassword"
        params = {
            'isAsync': 'true',
            'msisdn': publickey.encrypt(cellphone),
            'captcha': captcha,
            'sourceID': app_info['SOURCE_ID'],
            'imgcodeType': 2,
            'fingerPrint': fingerPrint,
            'fingerPrintDetail': fingerPrintDetail,
            '_': get_time_stamp(bit=13),
        }
        res = await sess.get(url, params=params)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"send sms failed: {res['message']}")

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

        sess = await self._sess
        app_info = await self._app_info
        publickey = await self._publickey
        url = "https://passport.migu.cn/authn/dynamicpassword"
        data = {
            'sourceID': app_info['SOURCE_ID'],
            'appType': 0,
            'relayState': '',
            'msisdn': publickey.encrypt(cellphone),
            'securityCode': 4053,
            'captcha': captcha,
            'imgcodeType': 2,
            'dynamicPassword': publickey.encrypt(verify_code),
            'fingerPrint': fingerPrint,
            'fingerPrintDetail': fingerPrintDetail,
            'isAsync': 'true',
        }
        res = await sess.post(url, data=data)
        res = await res.json(content_type=None)
        if res["status"] != 2000:
            raise RuntimeError(f"log in by sms failed: {res['message']}")
        await self._verify_token(
            res["result"]["redirectURL"],
            res["result"]["token"],
            "SMS_CODE",
        )
