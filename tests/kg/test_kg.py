import asyncio

from music_api import kg


async def _test() -> None:
    api = kg.API()
    try:
        song = (await api.search("周杰伦"))[0]
        status, url = await song.fetch()
        assert status == song.Status.Success
    finally:
        await api.deinit()


def test_kg() -> None:
    asyncio.get_event_loop().run_until_complete(_test())
