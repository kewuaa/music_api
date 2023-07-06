import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from random import choice
from typing import Awaitable, Callable, Optional

import aiofiles
import aiohttp

user_agents: Optional[list[str]] = None


class Template(ABC):
    """ api template."""

    @dataclass(order=False, eq=False, repr=False)
    class Song:
        """ song."""

        class Status(IntEnum):
            """ status."""

            Success = 0
            NeedLogin = 1
            NeedVIP = 2
        url: str = ""
        status: Status = Status.Success

    @dataclass(order=False, eq=False, repr=False)
    class SongInfo:
        """ information of song."""

        desc: str = ""
        img_url: str = ""
        id: str = ""
        master: "Template" = None

    @dataclass(order=False, eq=False, repr=False)
    class LoginHandleT:
        """ handle for log in."""

        QR: Optional[Callable[[None], Awaitable[None]]] = None
        PWD: Optional[
            tuple[
                Optional[Callable[[None], Awaitable[bytes]]],
                Callable[[str, str, Optional[str]], Awaitable[None]]
            ]
        ] = None
        SMS: Optional[
            tuple[
                Optional[Callable[[None], Awaitable[bytes]]],
                Callable[[str, Optional[str]], Awaitable[None]],
                Callable[[str, str, Optional[str]], Awaitable[None]]
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

        self._loop = loop = asyncio.get_event_loop() if loop is None else loop
        self._sess: Awaitable[aiohttp.ClientSession]  = \
            loop.create_task(self._init_sess())

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
    async def search(self, keyword: str) -> list:
        """ search song by keyword.

        :param name: keyword to search
        :return: list of search result
        """

        raise NotImplementedError


    @abstractmethod
    async def fetch_song(self, _id: str) -> Song:
        """ fetch song by id.

        :param _id: id of the song to fetch
        :return: Song object
        """

        raise NotImplementedError
