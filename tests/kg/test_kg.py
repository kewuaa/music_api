import asyncio

from music_api import kg


async def _test() -> None:
    try:
        api = kg.API()
        songs = await api.search("周杰伦")
        song = await api.fetch_song(songs[0])
        assert song.status == song.Status.Success
    finally:
        await api.deinit()


def test_kg() -> None:
    asyncio.get_event_loop().run_until_complete(_test())
