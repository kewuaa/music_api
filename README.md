# music_api
some apis to fetch music  
it includes
* [kugou](https://www.kugou.com/)
* [kuwo](http://www.kuwo.cn/)
* [wangyiyun](https://music.163.com/)
* [migu](https://music.migu.cn/v3)
* [qianqian](https://music.91q.com/)

# examples

```python
import asyncio

from music_api import Template, migu


async def main() -> None:
    api = migu.API()
    songs = await api.search("enemy")
    assert songs
    song = songs[0]
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
