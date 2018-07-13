# -*- coding: utf-8 -*-

import os
import unittest

from unittest.mock import Mock, patch

import bgmi

from bgmi.lib.controllers import *
from bgmi.website import DataSource
from bgmi.main import setup
from functools import partial
import json

with open('./tests/data/bangumi.json', 'r', encoding='utf8') as f:
    bgm_data = json.load(f)
    pass
with open('./tests/data/subtitle.json', 'r', encoding='utf8') as f:
    subtitle_data = json.load(f)
    pass
with open('./tests/data/fetch-bangumi-with-id.json', 'r', encoding='utf8') as f:
    episode_data = json.load(f)
    pass

Mock(return_value=())

search_result = [
    {
        'name'    : "路人女主的养成方法",
        'download': 'magnet:?xt=urn:btih:what ever',
        'title'   : "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
        'episode' : 12
    },
]


def fetch(data_source, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
    if bangumi_id in episode_data[data_source]:
        return episode_data[data_source][bangumi_id]
    else:
        return []


fetch_episode_of_bangumi = lambda data_source: partial(fetch, data_source=data_source)
fetch_bangumi_calendar_and_subtitle_group = lambda data: Mock(return_value=(bgm_data[data], subtitle_data[data]))
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
with open('./tests/data/bangumi-tv.json', 'r', encoding='utf8') as f:
    bgm_tv_data = json.load(f)


@patch('bgmi.website.requests.get', Mock(return_value=Mock(json=Mock(return_value=bgm_tv_data))))
@patch('bgmi.website.DATA_SOURCE_MAP', DATA_SOURCE_MAP)
class ControllersTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bangumi_name_1 = '海贼王'
        cls.bangumi_name_2 = "名侦探柯南"
        cls.source = DataSource()

    def test_a_cal(self):
        r = self.source.bangumi_calendar()
        self.assertIsInstance(r, dict)
        for day in r.keys():
            self.assertIn(day.lower(), [x.lower() for x in Bangumi.week])
            self.assertIsInstance(r[day], list)
            for bangumi in r[day]:
                self.assertIn("status", bangumi)
                self.assertIn("subtitle_group", bangumi)
                self.assertIn("data_source", bangumi)
                self.assertIn("name", bangumi)
                self.assertIn("keyword", bangumi)
                self.assertIn("update_time", bangumi)
                self.assertIn("cover", bangumi)

    def test_b_add(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')

    def test_c_mark(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')

        r = mark(self.bangumi_name_1, 1)
        self.assertEqual(r['status'], 'success')
        r = mark(self.bangumi_name_1, None)
        self.assertEqual(r['status'], 'info')
        r = mark(self.bangumi_name_2, 0)
        self.assertEqual(r['status'], 'error')

    def test_d_delete(self):
        r = delete()
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_2)
        self.assertEqual(r['status'], 'error')
        r = delete(clear_all=True, batch=True)
        self.assertEqual(r['status'], 'warning')

    def test_e_search(self):
        r = search(self.bangumi_name_1, dupe=False)

    def test_fetch_episode_with_filter(self):

        pass
