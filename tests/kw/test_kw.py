import os
import json
import asyncio
from pathlib import Path

from music_api import kw
with open(Path(__file__).parent / "account", "r") as f:
    account = json.load(f)


async def show(img: bytes) -> None:
    path = Path(__file__).parent / "img.jpg"
    with open(path, "wb") as f:
        f.write(img)
    os.system(f"explorer {path}")


async def _test() -> None:
    try:
        api = kw.API()
        songs = await api.search("周杰伦")
        song = await api.fetch_song(songs[0])
        assert song.status == song.Status.NeedVIP
    finally:
        await api.deinit()


async def _test_login_by_pwd() -> None:
    try:
        api = kw.API()
        fetch_captcha, login_by_pwd = api.login.PWD
        await show(await fetch_captcha())
        await login_by_pwd(account["id"], account["password"], input("captcha is:"))
    finally:
        await api.deinit()


async def _test_login_by_sms() -> None:
    try:
        api = kw.API()
        fetch_captcha, send_sms, login_by_sms = api.login.SMS
        await show(await fetch_captcha())
        captcha = input("captcha is:")
        await send_sms(account["id"], captcha)
        verify_code = input("verify code is:")
        await login_by_sms(account["id"], verify_code, captcha)
    finally:
        await api.deinit()


def test_kw() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test())
    loop.run_until_complete(_test_login_by_pwd())
    loop.run_until_complete(_test_login_by_sms())
