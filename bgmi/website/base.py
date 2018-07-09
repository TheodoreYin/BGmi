# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import re
from collections import defaultdict
from itertools import chain

from six import text_type

from bgmi.config import MAX_PAGE, GLOBAL_FILTER, ENABLE_GLOBAL_FILTER
from bgmi.lib.models import (Subtitle, STATUS_FOLLOWED, STATUS_UPDATED,
                             Bangumi, STATUS_UPDATING)
from bgmi.utils import (parse_episode, print_warning, print_info,
                        test_connection, download_cover, convert_cover_url_to_path)


class BaseWebsite(object):
    cover_url = ''
    parse_episode = staticmethod(parse_episode)

    @staticmethod
    def save_data(data):
        """
        save bangumi dict to database

        :type data: dict
        """
        b, obj_created = Bangumi.get_or_create(name=data['name'], defaults=data)
        if not obj_created:
            b.status = STATUS_UPDATING
            b.subtitle_group = Bangumi(**data).subtitle_group
            b.cover = data['cover']
            b.save()

    def fetch(self, save=False, group_by_weekday=True):
        bangumi_result, subtitle_group_result = self.fetch_bangumi_calendar_and_subtitle_group()
        Bangumi.delete_all()
        if subtitle_group_result:
            for subtitle_group in subtitle_group_result:
                (Subtitle.insert({Subtitle.id: text_type(subtitle_group['id']),
                                  Subtitle.name: text_type(subtitle_group['name'])})
                 .on_conflict_replace()).execute()
        if not bangumi_result:
            print('no result return None')
            return []

        for bangumi in bangumi_result:
            bangumi['cover'] = self.cover_url + bangumi['cover']

        if save:
            for bangumi in bangumi_result:
                self.save_data(bangumi)

        if group_by_weekday:
            result_group_by_weekday = defaultdict(list)
            for bangumi in bangumi_result:
                result_group_by_weekday[bangumi['update_time'].lower()].append(bangumi)
            bangumi_result = result_group_by_weekday
        return bangumi_result

    @staticmethod
    def followed_bangumi():
        """

        :return: list of bangumi followed
        :rtype: list[dict]
        """
        weekly_list_followed = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
        weekly_list_updated = Bangumi.get_updating_bangumi(status=STATUS_UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi['subtitle_group'] = [{'name': x['name'],
                                              'id': x['id']} for x in
                                             Subtitle.get_subtitle_by_id(bangumi['subtitle_group'].split(', '))]
        return weekly_list

    def bangumi_calendar(self, force_update=False, save=True, cover=None):
        """

        :param force_update:
        :type force_update: bool

        :param save: set true to enable save bangumi data to database
        :type save: bool

        :param cover: list of cover url (of scripts) want to download
        :type cover: list[str]
        """
        if force_update and not test_connection():
            force_update = False
            print_warning('Network is unreachable')

        if force_update:
            print_info('Fetching bangumi info ...')
            weekly_list = self.fetch(save=save)
        else:
            weekly_list = Bangumi.get_updating_bangumi()

        if not weekly_list:
            print_warning('Warning: no bangumi schedule, fetching ...')
            weekly_list = self.fetch(save=save)

        if cover is not None:
            # download cover to local
            cover_to_be_download = cover
            for daily_bangumi in weekly_list.values():
                for bangumi in daily_bangumi:
                    _, file_path = convert_cover_url_to_path(bangumi['cover'])

                    if not os.path.exists(file_path):
                        cover_to_be_download.append(bangumi['cover'])

            if cover_to_be_download:
                print_info('Updating cover ...')
                download_cover(cover_to_be_download)

        return weekly_list

    def search_by_keyword(self, keyword, count):  # pragma: no cover
        """
        return a list of dict with at least 4 key: download, name, title, episode
        example:
        ```
            [
                {
                    'name':"路人女主的养成方法",
                    'download': 'magnet:?xt=urn:btih:what ever',
                    'title': "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
                    'episode': 12
                },
            ]

        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from data_source
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise NotImplementedError

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
