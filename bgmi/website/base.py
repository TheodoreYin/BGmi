# coding=utf-8

from bgmi.config import MAX_PAGE
from bgmi.utils import (parse_episode)


class BaseWebsite(object):
    cover_url = ''
    parse_episode = staticmethod(parse_episode)

    def fetch_bangumi_calendar_and_subtitle_group(self):  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        example:
        ```
            [
                {
                    "status": 0,
                    "subtitle_group": [
                        "123",
                        "456"
                    ],
                    "name": "名侦探柯南",
                    "keyword": "1234", #bangumi id
                    "update_time": "Sat",
                    "cover": "data/images/cover1.jpg"
                },
            ]
        ```

        list of subtitle group dict:
        example:
        ```
            [
                {
                    'id': '233',
                    'name': 'bgmi字幕组'
                }
            ]
        ```


        :return: list of bangumi, list of subtitile group
        :rtype: (list[dict], list[dict])
        """
        raise NotImplementedError

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):  # pragma: no cover
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
                    "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                    "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                    "episode": 0,
                    "time": 1503301292
                },
            ]
        ```

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :type subtitle_list: list
        :param max_page: how many page you want to crawl if there is no subtitle list
        :type max_page: int
        :return: list of bangumi
        :rtype: list[dict]
        """
        raise NotImplementedError
