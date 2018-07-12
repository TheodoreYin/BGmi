# coding=utf-8
import glob
import json
import os
import os.path
import re
import shutil
import unittest
import unittest.mock
from unittest.mock import patch, Mock
from types import SimpleNamespace

import bgmi.downloader
import bgmi.lib.download
from bgmi.downloader.base import BaseDownloadService

download_history = []


class DevDownloadDelegate(BaseDownloadService):

    def __init__(self, *args, **kwargs):
        super(DevDownloadDelegate, self).__init__(**kwargs)
        """
        self.name = download_obj.name
        self.torrent = download_obj.download
        self.overwrite = overwrite
        self.save_path = save_path
        self.episode = download_obj.episode
        self.return_code = 0
        """

    def download(self):
        download_history.append({
            'name'      : self.name,
            'torrent'   : self.torrent,
            'save_path' : self.save_path,
            "episode"   : self.episode,
            'overwrite ': self.overwrite,
        })
        with open(self.save_path + '/torrent', 'w', encoding='utf8') as f:
            f.write(self.torrent)
        pass

    @staticmethod
    def install():
        pass

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        pass


MockDownloadDelegate = Mock(spec=BaseDownloadService)


class D:
    def get(self, *args, **kwargs):
        return DevDownloadDelegate

    def __getitem__(self, item):
        return DevDownloadDelegate

    def __contains__(self, item):
        return True


# d = D()
# print(d[233])

import pathlib


class UtilsTest(unittest.TestCase):
    def setUp(self):
        pass

    @patch('bgmi.lib.download.SAVE_PATH', './test_dir')
    def test_download_file(self):
        with patch('bgmi.lib.download.DOWNLOAD_DELEGATE_DICT', D()) as m:
            # m.assert_called_with('https://hello world')
            data = [{'title'   : 'title_1',
                     'download': 'download_2',
                     'episode' : '123',
                     'name'    : 'name_4', }]
            bgmi.lib.download.download_prepare(data)
            download = download_history[0]
            self.assertEqual(pathlib.Path(download['save_path']), pathlib.Path('./test_dir') / 'name_4' / '123')
            with open(download['save_path'] + '/torrent', 'r', encoding='utf8') as f:
                self.assertEqual(download['torrent'], f.read())
