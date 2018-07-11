# coding=utf-8

import configparser
import os
import re
import unittest
import unittest.mock

from unittest.mock import patch, Mock
from bgmi import utils


class UtilsTest(unittest.TestCase):

    def download_cover(self):
        pass

    def test_download_file(self):
        with patch('bgmi.utils.download_file') as m:
            m.return_value = 'mock'
            self.assertEqual(utils.download_file('https://hello world'), 'mock')
            m.assert_called_with('https://hello world')

    def test_parse_episode(self):
        with open('tests/data/episode', 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line for line in lines if line]
        for line in lines:
            episode, title = line.split(' ', 1)
            title = title.rstrip()
            episode = int(episode)
            self.assertEqual(episode, utils.parse_episode(title), msg=title)

        return 0

    def test_chinese_to_arabic(self):
        test_case = [
            ['八', 8],
            ['十一', 11],
            ['一百二十三', 123],
            ['一千二百零三', 1203],
            ['一万一千一百零一', 11101],
        ]
        for raw, result in test_case:
            self.assertEqual(utils.chinese_to_arabic(raw), result)

    def test_normalize_path(self):
        self.assertEqual(utils.normalize_path('http://hello? world:/233.qq'), 'http/hello world/233.qq')
