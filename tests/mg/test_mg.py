import os
import json
import asyncio
from pathlib import Path

from music_api import mg
account_path = Path(__file__).parent / "account"
with open(account_path, "r") as f:
    account = json.load(f)


async def show(img: bytes) -> None:
    path = Path(__file__).parent / "qrcode.jpg"
    with open(path, "wb") as f:
        f.write(img)
    os.system(f"explorer {path}")


async def _test_search() -> None:
    try:
        api = mg.API()
        songs = await api.search("张碧晨")
        assert songs
    finally:
        await api.deinit()


async def _test_login_by_qr() -> None:
    try:
        api = mg.API()
        login_by_qr = api.login.QR
        if login_by_qr is not None:
            await login_by_qr(show)
        songs = await api.search("张碧晨")
        song = await api.fetch_song(songs[0])
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


async def _test_login_by_pwd() -> None:
    try:
        api = mg.API()
        if api.login.QR is None:
            return
        fetch_captch, login_by_pwd = api.login.PWD
        if fetch_captch is not None:
            await show(await fetch_captch())
        captcha = input("captcha is:")
        try:
            await login_by_pwd(account["id"], account["password"], captcha)
        except RuntimeError as e:
            print(e)
            return
        songs = await api.search("张碧晨")
        song = await api.fetch_song(songs[0].id)
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


async def _test_login_by_sms() -> None:
    try:
        api = mg.API()
        if api.login.SMS is None:
            return
        fetch_captch, send_sms, login_by_sms = api.login.SMS
        if fetch_captch is not None:
            await show(await fetch_captch())
        captcha = input("captcha is:")
        await send_sms(account["id"], captcha)
        verify_code = input("verify_code is:")
        await login_by_sms(account["id"], verify_code, captcha)
        songs = await api.search("张碧晨")
        song = await api.fetch_song(songs[0].id)
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


def test_all() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test_search())
    loop.run_until_complete(_test_login_by_qr())
    loop.run_until_complete(_test_login_by_pwd())
    loop.run_until_complete(_test_login_by_sms())
