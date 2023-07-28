import asyncio
import json
from pathlib import Path

from music_api import qianqian
with open(Path(__file__).parent / "account", "r") as f:
    account = json.load(f)


async def _test() -> None:
    api = qianqian.API()
    try:
        song = (await api.search("张碧晨"))[0]
        status, url = await song.fetch()
        assert status == song.Status.Success
    finally:
        await api.deinit()


async def _test_login_by_pwd() -> None:
    api = qianqian.API()
    try:
        _, login_by_pwd = api.login.PWD
        await login_by_pwd(account["id"], account["password"], "")
    finally:
        await api.deinit()


def test_all() -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test())
    loop.run_until_complete(_test_login_by_pwd())
