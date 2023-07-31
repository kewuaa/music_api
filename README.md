# music_api
some apis to fetch music  
it includes
* [kugou](https://www.kugou.com/)
* [kuwo](http://www.kuwo.cn/)
* [wangyiyun](https://music.163.com/)
* [migu](https://music.migu.cn/v3)
* [qianqian](https://music.91q.com/)

# examples

## fetch song

```python
import asyncio

from music_api import Template, migu


async def main() -> None:
    api = migu.API()
    songs = await api.search("enemy")
    assert songs
    song = songs[0]
    assert type(song) is Template.Song
    # Song object has fields:
    #     desc: simple description of the song
    #     url: url of song
    #     fetch: function to fetch song url
    #     owner: owner of the song, instance of Template
    assert song.url == ""
    status, url = await song.fetch()
    if status is Template.Song.Status.Success:
        print(url)
        assert song.url == url
    elif status is Template.Song.Status.NeedVIP:
        print("need vip")
    elif status is Template.Song.Status.NeedLogin:
        print("need log in")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
```

## log in

```python
import asyncio
from io import BytesIO

from music_api import Template, migu
from PIL import Image


async def show_img(img: bytes) -> None:
    f = BytesIO(img)
    img = Image.open(f)
    img.show()

async def main() -> None:
    api = migu.API()

    assert api.login.QR is not None
    login_by_qr = api.login.QR
    await login_by_qr(show_img)

    assert api.login.SMS is not None
    cellphone = input("cellphone is:")
    fetch_captcha, send_sms, login_by_sms = api.login.SMS
    captcha = ""
    if fetch_captcha is not None:
        await fetch_captcha()
        captcha = input("captcha is:")
    await send_sms(cellphone, captcha)
    verify_code = input("verify code is:")
    await login_by_sms(cellphone, verify_code, captcha)

    assert api.login.PWD is not None
    cellphone = input("cellphone is:")
    password = input("password is:")
    fetch_captcha, login_by_pwd = api.login.PWD
    captcha = ""
    if fetch_captcha is not None:
        await fetch_captcha()
        captcha = input("captcha is:")
    await login_by_pwd(cellphone, password, captcha)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
```
