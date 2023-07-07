import asyncio
import json
from pathlib import Path

from music_api import qianqian
with open(Path(__file__).parent / "account", "r") as f:
    account = json.load(f)


async def _test() -> None:
    try:
        api = qianqian.API()
        songs = await api.search("张碧晨")
        song = await api.fetch_song(songs[0])
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


async def _test_login_by_pwd() -> None:
    try:
        api = qianqian.API()
        _, login_by_pwd = api.login.PWD
        await login_by_pwd(account["id"], account["password"], None)
    finally:
        await api.deinit()


def test_all() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test())
    loop.run_until_complete(_test_login_by_pwd())
