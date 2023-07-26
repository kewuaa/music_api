import asyncio
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from random import choice
from typing import Any, Awaitable, Callable, Optional, Union, Coroutine

import aiofiles
import aiohttp

user_agents: Optional[list[str]] = None


class Template(ABC):
    """ api template."""

    @dataclass(order=False, eq=False, repr=False)
    class Song:
        """ song."""

        @dataclass(order=False, eq=False, repr=False)
        class Information:
            """ information of song."""

            desc: str = ""
            img_url: str = ""
            id: tuple = tuple()
            master: "Template" = None # pyright: ignore

        class Status(IntEnum):
            """ status."""

            Success = 0
            NeedLogin = 1
            NeedVIP = 2
        info: Information = Information()
        url: str = ""
        format: str = ""
        status: Status = Status.Success

    @dataclass(order=False, eq=False, repr=False)
    class LoginHandleT:
        """ handle for log in."""

        QR: Optional[
            Callable[
                [Callable[[bytes], Coroutine[Any, Any, None]]],
                Coroutine[Any, Any, None]
            ]
        ] = None
        PWD: Optional[
            tuple[
                Optional[Callable[[], Coroutine[Any, Any, bytes]]],
                Callable[[str, str, str], Coroutine[Any, Any, None]]
            ]
        ] = None
        SMS: Optional[
            tuple[
                Optional[Callable[[], Coroutine[Any, Any, bytes]]],
                Callable[[str, str], Coroutine[Any, Any, None]],
                Callable[[str, str, str], Coroutine[Any, Any, None]]
            ]
        ] = None
    login = LoginHandleT()

    def __init__(
        self,
        loop: Optional[asyncio.base_events.BaseEventLoop] = None
    ) -> None:
        """ initialize.

        :param loop: the event loop, optional.
        """

        self._loop = asyncio.get_event_loop() if loop is None else loop
        self._sess: Awaitable[aiohttp.ClientSession]  = \
            self._loop.create_task(self._init_sess())

    @staticmethod
    async def load_agents() -> str:
        """ load user agents.

        :return: user agent
        """

        global user_agents
        if user_agents is None:
            async with aiofiles.open(
                Path(__file__).parent / "user_agents.txt", "r"
            ) as f:
                user_agents = [line.strip() for line in await f.readlines()]
        return choice(user_agents)

    async def _init_sess(self) -> aiohttp.ClientSession:
        """ initialize session.

        :return: ClientSession
        """

        return aiohttp.ClientSession(
            loop=self._loop,
            headers={"user-agent": await self.load_agents()}
        )

    async def deinit(self) -> None:
        """ destruct."""

        # close the ClientSession
        sess = await self._sess
        if not sess.closed:
            await sess.close()

    @abstractmethod
    async def search(self, keyword: str) -> list[Song.Information]:
        """ search song by keyword.

        :param name: keyword to search
        :return: list of search result
        """

        raise NotImplementedError


    @abstractmethod
    async def fetch_song(self, info: Song.Information) -> Song:
        """ fetch song by SongInfo.

        :param info: SongInfo
        :return: Song object
        """

        raise NotImplementedError

    async def save_cookies(self, path: Union[str, Path]) -> None:
        """ save cookies."""

        sess = await self._sess
        with open(path, "wb") as f:
            pickle.dump(sess.cookie_jar._cookies, f) # pyright: ignore

    async def load_cookies(self, path: Union[str, Path]) -> None:
        """ load cookies."""

        sess = await self._sess
        with open(path, "rb") as f:
            sess.cookie_jar._cookies = pickle.load(f) # pyright: ignore
