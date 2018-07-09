# coding=utf-8
import os.path
import re
import time
from collections import defaultdict
from copy import deepcopy

import requests
from fuzzywuzzy import fuzz
from hanziconv import HanziConv
from six import text_type

from bgmi.config import MAX_PAGE, ENABLE_GLOBAL_FILTER, GLOBAL_FILTER
from bgmi.lib import models
from bgmi.lib.models import STATUS_UPDATING
from bgmi.lib.models import Bangumi, Subtitle, Filter
from bgmi.utils import test_connection, print_warning, print_info, download_cover, convert_cover_url_to_path
from bgmi.website.bangumi_moe import BangumiMoe
from bgmi.website.mikan import Mikanani
from bgmi.website.share_dmhy import DmhySource

DATA_SOURCE_MAP = {
    'mikan_project': Mikanani(),
    'bangumi_moe': BangumiMoe(),
    'dmhy': DmhySource(),
}


def cleanBangumiDict(bangumi):
    """

    :type bangumi: dict
    """
    return {
        "status": bangumi['status'],
        "subtitle_group": bangumi['subtitle_group'],
        "name": bangumi['name'],
        "keyword": bangumi['keyword'],  # bangumi id
        "update_time": bangumi['update_time'],
        "cover": bangumi['cover']
    }


def findMostSimilarBangumi(name, bangumi_list):
    """

    :type bangumi_list: list[dict]
    :type name: str
    """
    m = 0
    max_bangumi = None
    name = HanziConv.toSimplified(name)
    for index, bangumi in enumerate(bangumi_list):
        n2 = HanziConv.toSimplified(bangumi['name'])
        s = fuzz.partial_ratio(name, n2)
        if s > 50:
            if s > m:
                m = s
                max_bangumi = bangumi
    return max_bangumi


def mergeDataSource(origin_bangumi_list, data_source_bangumi_list, source):
    """

    :type source: str
    :type data_source_bangumi_list: list[dict]
    :type origin_bangumi_list: list[dict]
    """
    data_source_bangumi_list = deepcopy(data_source_bangumi_list)
    for bangumi in origin_bangumi_list:
        m = findMostSimilarBangumi(bangumi['name'], data_source_bangumi_list)
        if m:
            data_source_bangumi_list.remove(m)
            bangumi['data_source'][source] = cleanBangumiDict(m)
    for bangumi in data_source_bangumi_list:
        bangumi['data_source'] = {source: deepcopy(bangumi)}
    return data_source_bangumi_list


def init_data():
    r = requests.get('https://api.bgm.tv/calendar')
    r = r.json()
    bangumi_tv_weekly_list = []

    for day in r:
        for index, item in enumerate(day['items']):
            day['items'][index] = {
                'name': item['name_cn'],
                'update_time': day['weekday']['en'].capitalize(),
                'keyword': item['id'],
                "status": models.STATUS_UPDATING,
                "cover": '',
                'data_source': {},
            }
        bangumi_tv_weekly_list += day['items']

    left = []
    subtitle = {}
    for data_source_id, data_source in DATA_SOURCE_MAP.items():
        bangumi_list, subtitle_list = data_source.fetch_bangumi_calendar_and_subtitle_group()
        subtitle[data_source_id] = subtitle_list
        left += mergeDataSource(bangumi_tv_weekly_list,
                                bangumi_list,
                                data_source_id)
    import json
    with open('./tmp/f.json', 'w+', encoding='utf8') as f:
        json.dump(bangumi_tv_weekly_list, f, ensure_ascii=False, indent=2)
    with open('./tmp/left.json', 'w+', encoding='utf8') as f:
        json.dump(left, f, ensure_ascii=False, indent=2)
    # return bangumi_tv_weekly_list + left, None
    return bangumi_tv_weekly_list + left, subtitle


class DataSource():
    class utils:

        @staticmethod
        def remove_duplicated_bangumi(result):
            """

            :type result: list[dict]
            """
            ret = []
            episodes = list({i['episode'] for i in result})
            for i in result:
                if i['episode'] in episodes:
                    ret.append(i)
                    del episodes[episodes.index(i['episode'])]

            return ret

        @staticmethod
        def filter_keyword(data, regex=None):
            """

            :type regex: str
            :param data: list of bangumi dict
            :type data: list[dict]
            """
            if regex:
                try:
                    match = re.compile(regex)
                    data = [s for s in data if match.findall(s['title'])]
                except re.error as e:
                    if os.getenv('DEBUG'):  # pragma: no cover
                        import traceback
                        traceback.print_exc()
                        raise e
                    return data

            if not ENABLE_GLOBAL_FILTER == '0':
                data = list(filter(lambda s: all(map(lambda t: t.strip().lower() not in s['title'].lower(),
                                                     GLOBAL_FILTER.split(','))), data))

            return data

    def fetch(self, save=False, group_by_weekday=True):
        bangumi_result, subtitle_group_result = init_data()
        Bangumi.delete_all()
        for data_source_id, subtitle_group_list in subtitle_group_result.items():
            for subtitle_group in subtitle_group_list:
                (Subtitle.insert({Subtitle.id: text_type(subtitle_group['id']),
                                  Subtitle.name: text_type(subtitle_group['name']),
                                  Subtitle.data_source: data_source_id})
                 .on_conflict_replace()).execute()
        if not bangumi_result:
            print('no result return None')
            return []

        # todo
        for bangumi in bangumi_result:
            bangumi['cover'] = bangumi['cover']

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
    def save_data(data):
        """
        save bangumi dict to database

        :type data: dict
        """
        b, obj_created = Bangumi.get_or_create(name=data['name'], defaults=data)
        if not obj_created:
            b.status = STATUS_UPDATING
            b.cover = data['cover']
            b.save()

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

    def get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=int(MAX_PAGE)):
        """

        :type max_page: str
        :param max_page:
        :type bangumi: object
        :type ignore_old_row: bool
        :param ignore_old_row:
        :type bangumi: Bangumi
        :param subtitle:
        :type subtitle: bool
        """
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)

        if followed_filter_obj and subtitle:
            subtitle_group = followed_filter_obj.subtitle
        else:
            subtitle_group = None

        if followed_filter_obj and subtitle:
            include = followed_filter_obj.include
        else:
            include = None

        if followed_filter_obj and subtitle:
            exclude = followed_filter_obj.exclude
        else:
            exclude = None

        if followed_filter_obj and subtitle:
            regex = followed_filter_obj.regex
        else:
            regex = None
        if followed_filter_obj and subtitle:
            source = followed_filter_obj.data_source
        else:
            source = None

        data = [i for i in self.fetch_episode(bangumi_obj=bangumi,
                                              subtitle_group=subtitle_group,
                                              include=include,
                                              source=source,
                                              exclude=exclude,
                                              regex=regex,
                                              max_page=int(max_page))
                if i['episode'] is not None]

        if ignore_old_row:
            data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        if data:
            bangumi = max(data, key=lambda _i: _i['episode'])
            return bangumi, data
        else:
            return {'episode': 0}, []

    def fetch_episode(self, subtitle_group=None,
                      include=None,
                      exclude=None,
                      regex=None,
                      source=None,
                      bangumi_obj=None,
                      max_page=int(MAX_PAGE)):
        """
        :type bangumi_obj: Bangumi
        :type subtitle_group: str
        :type include: str
        :type exclude: str
        :type regex: str
        :type max_page: int
        """
        result = []
        _id = bangumi_obj.id
        name = bangumi_obj.name
        max_page = int(max_page)

        if source:
            source = source.split(', ')
        else:
            source = bangumi_obj.data_source.keys()
        response_data = []
        if subtitle_group and subtitle_group.split(', '):
            condition = [x.strip() for x in subtitle_group.split(', ')]
            subtitle_group = Subtitle.select(Subtitle.name, Subtitle.data_source) \
                .where(Subtitle.name.in_(condition) and Subtitle.data_source.in_(source))
            condition = defaultdict(list)
            for subtitle in subtitle_group:
                condition[subtitle.data_source].append(subtitle.name)
            for source, subtitle_group in condition.items():
                response_data += DATA_SOURCE_MAP[source].fetch_episode_of_bangumi(
                    bangumi_id=bangumi_obj.data_source[source]['keyword'],
                    subtitle_list=subtitle_group)
        else:
            for i in source:
                response_data += DATA_SOURCE_MAP[i].fetch_episode_of_bangumi(
                    bangumi_id=bangumi_obj.data_source[i]['keyword'],
                    max_page=max_page)

        for info in response_data:
            if '合集' not in info['title']:
                info['name'] = name
                result.append(info)

        if include:
            include_list = list(map(lambda s: s.strip(), include.split(',')))
            result = list(filter(lambda s: True if all(map(lambda t: t in s['title'],
                                                           include_list)) else False, result))

        if exclude:
            exclude_list = list(map(lambda s: s.strip(), exclude.split(',')))
            result = list(filter(lambda s: True if all(map(lambda t: t not in s['title'],
                                                           exclude_list)) else False, result))

        result = self.utils.filter_keyword(data=result, regex=regex)
        return result
