import os
import json
import asyncio
from pathlib import Path

from music_api import wyy
with open(Path(__file__).parent / "account", "r") as f:
    account = json.load(f)


async def show(img: bytes) -> None:
    path = Path(__file__).parent / "qrcode.jpg"
    with open(path, "wb") as f:
        f.write(img)
    os.system(f"explorer {path}")


async def _test() -> None:
    try:
        api = wyy.API()
        songs = await api.search("周杰伦")
        assert songs
        song = await api.fetch_song(songs[0].id)
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


async def _test_login_by_qrcode() -> None:
    try:
        api = wyy.API()
        login_by_qrcode = api.login.QR
        assert login_by_qrcode is not None
        await login_by_qrcode(show)
    finally:
        await api.deinit()


async def _test_login_by_sms() -> None:
    try:
        api = wyy.API()
        if api.login.SMS is None:
            return
        fetch_captch, send_sms, login_by_sms = api.login.SMS
        if fetch_captch is not None:
            await show(await fetch_captch())
        await send_sms(account["cellphone"], None)
        verify_code = input("verify code is:")
        await login_by_sms(account["cellphone"], verify_code, None)
    finally:
        await api.deinit()


def test_all() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test())
    loop.run_until_complete(_test_login_by_qrcode())
    # loop.run_until_complete(_test_login_by_sms())
