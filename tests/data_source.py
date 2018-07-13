# -*- coding: utf-8 -*-
import time
import os
import unittest

from unittest.mock import Mock, patch

import bgmi

from bgmi.website import DataSource
from functools import partial
import json

from bgmi.lib.models import Subtitle, Bangumi
from bgmi.utils import convert_cover_url_to_path

with open('./tests/data/bangumi.json', 'r', encoding='utf8') as f:
    bgm_data = json.load(f)
with open('./tests/data/subtitle.json', 'r', encoding='utf8') as f:
    subtitle_data = json.load(f)
with open('./tests/data/fetch-bangumi-with-id.json', 'r', encoding='utf8') as f:
    episode_data = json.load(f)
with open('./tests/data/bangumi-tv.json', 'r', encoding='utf8') as f:
    bgm_tv_data = json.load(f)
with open('./tests/data/inited_data.json', 'r', encoding='utf8') as f:
    inited_data = json.load(f)
search_result = [
    {
        'name'    : "路人女主的养成方法",
        'download': 'magnet:?xt=urn:btih:what ever',
        'title'   : "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
        'episode' : 12
    },
]


def fetch(data_source, bangumi_id, subtitle_list=None, max_page=3):
    if bangumi_id in episode_data[data_source]:
        return episode_data[data_source][bangumi_id]
    else:
        return []


fetch_episode_of_bangumi = lambda data_source: partial(fetch, data_source=data_source)
fetch_bangumi_calendar_and_subtitle_group = lambda data: Mock(return_value=(bgm_data[data],
                                                                            subtitle_data[data]))

DATA_SOURCE_MAP = {
    'mikan_project': Mock(
        fetch_bangumi_calendar_and_subtitle_group=fetch_bangumi_calendar_and_subtitle_group('mikan_project'),
        fetch_episode_of_bangumi=fetch_episode_of_bangumi('mikan_project'),
        search_by_keyword=Mock(return_value=[])
    ),
    'bangumi_moe'  : Mock(
        fetch_bangumi_calendar_and_subtitle_group=fetch_bangumi_calendar_and_subtitle_group('bangumi_moe'),
        fetch_episode_of_bangumi=fetch_episode_of_bangumi('bangumi_moe'),
        search_by_keyword=Mock(return_value=[])
    ),
    'dmhy'         : Mock(
        fetch_bangumi_calendar_and_subtitle_group=fetch_bangumi_calendar_and_subtitle_group('dmhy'),
        fetch_episode_of_bangumi=fetch_episode_of_bangumi('dmhy'),
        search_by_keyword=Mock(return_value=[])
    ),
}


@patch('bgmi.website.requests.get', Mock(return_value=Mock(json=Mock(return_value=bgm_tv_data))))
@patch('bgmi.website.test_connection', Mock(return_value=True))
@patch('bgmi.website.DATA_SOURCE_MAP', DATA_SOURCE_MAP)
class DataSourceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bangumi_name_1 = '海贼王'
        cls.bangumi_name_2 = "名侦探柯南"
        cls.source = DataSource()

    @patch('bgmi.website.requests.get', Mock(return_value=Mock(json=Mock(return_value=bgm_tv_data))))
    @patch('bgmi.website.test_connection', Mock(return_value=True))
    @patch('bgmi.website.DATA_SOURCE_MAP', DATA_SOURCE_MAP)
    def test_fetch(self):
        with patch('bgmi.website.init_data') as init_data:
            init_data.return_value = (inited_data, subtitle_data)
            d = self.source.fetch()
            for key, value in subtitle_data.items():
                for v in value:
                    Subtitle.get(id=v['id'], name=v['name'], data_source=key)
            for key, value in d.items():
                for bangumi in value:
                    self.assertIn(bangumi, inited_data)
            for bangumi in inited_data:
                self.assertIn(bangumi, d[bangumi['update_time'].lower()])
            d = self.source.fetch(group_by_weekday=False)
            self.assertEqual(d, inited_data)
        # todo: subtitle change name

    def test_bangumi_calendar(self):
        print('bangumi_calendar')
        print(time.time())

        with patch('bgmi.website.init_data') as init_data:
            with patch('bgmi.website.download_cover') as m:
                init_data.return_value = (inited_data, subtitle_data)
                d = self.source.bangumi_calendar(cover=True, save=False)
                # todo: test cover download
                l = []
                li = m.call_args[0]
                # for bangumi in inited_data:
                #     self.assertIn(bangumi['cover'], li)
        print(time.time())

    def est_get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=int(3)):
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)  # type : (Filter, bool)

        return {'episode': 0}, []

    def fetch_episode(self, subtitle_group=None,
                      include=None,
                      exclude=None,
                      regex=None,
                      source=None,
                      bangumi_obj=None,
                      max_page=int(3)):
        b = Bangumi.get(name=self.bangumi_name_1)
        self.source.fetch_episode(bangumi_obj=b)
        # todo :global filter
        # todo :include filter
        # todo :exclude filter

        # todo :source only filter
        # todo :subtitle group only filter
        # todo :subtitle group and source filter

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
                                              'id'  : x['id']} for x in
                                             Subtitle.get_subtitle_from_data_source_dict(bangumi['data_source'])]
        return weekly_list


if __name__ == '__main__':
    unittest.main()
