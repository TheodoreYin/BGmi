# coding=utf-8

import os
import time
from collections import defaultdict

import peewee
from peewee import IntegerField, FixedCharField, TextField
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import JSONField

import bgmi.config

# from typing import List

# bangumi status
STATUS_UPDATING = 0
STATUS_END = 1
BANGUMI_STATUS = (STATUS_UPDATING, STATUS_END)

# bangumi type
TYPE_MAINLINE = 0
TYPE_LEFT = 1

# subscription status
# Followed bangumi status
STATUS_DELETED = 0
STATUS_FOLLOWED = 1
STATUS_UPDATED = 2
FOLLOWED_STATUS = (STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED)

# download status
STATUS_NOT_DOWNLOAD = 0
STATUS_DOWNLOADING = 1
STATUS_DOWNLOADED = 2
DOWNLOAD_STATUS = (STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, STATUS_DOWNLOADED)

DoesNotExist = peewee.DoesNotExist

db = peewee.SqliteDatabase(bgmi.config.DB_PATH)


class NeoDB(peewee.Model):
    class Meta:
        database = db


class Bangumi(NeoDB):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True, null=False)
    update_time = FixedCharField(5, null=False)
    keyword = TextField()
    status = IntegerField(default=0)
    cover = TextField()
    type = TextField(null=False)
    data_source = JSONField(default=lambda: {})  # type: dict

    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, **kwargs):
        super(NeoDB, self).__init__(**kwargs)

        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexpected update time %s' % update_time)
        self.update_time = update_time
        if isinstance(kwargs.get('subtitle_group'), list):
            self.subtitle_group = ', '.join(kwargs.get('subtitle_group', []))

    @classmethod
    def delete_all(cls):
        un_updated_bangumi = Followed.select() \
            .where(Followed.updated_time > (int(time.time()) - 2 * 7 * 24 * 3600))  # type: list[Followed]
        if os.getenv('DEBUG'):  # pragma: no cover
            print('ignore updating bangumi', [x.bangumi_name for x in un_updated_bangumi])

        cls.update(status=STATUS_END) \
            .where(cls.name.not_in([x.bangumi_name for x in un_updated_bangumi])).execute()  # do not mark updating bangumi as STATUS_END

    @classmethod
    def get_updating_bangumi(cls, status=None, order=True):
        if status is None:
            data = cls.select(Followed.status, Followed.episode, cls, ) \
                .join(Followed, peewee.JOIN['LEFT_OUTER'], on=(cls.name == Followed.bangumi_name)) \
                .where(cls.status == STATUS_UPDATING).dicts()
        else:
            data = cls.select(Followed.status, Followed.episode, cls, ) \
                .join(Followed, peewee.JOIN['LEFT_OUTER'], on=(cls.name == Followed.bangumi_name)) \
                .where((cls.status == STATUS_UPDATING) & (Followed.status == status)).dicts()

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))
        else:
            weekly_list = list(data)

        return weekly_list

    @classmethod
    def get_all_bangumi(cls):
        return cls.select().dicts()


class Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)

    class Meta:
        database = db

    @classmethod
    def delete_followed(cls, batch=True):
        q = cls.delete()
        if not batch:
            if not input('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ') == 'y':
                return False
        q.execute()
        return True

    @classmethod
    def get_all_followed(cls, status=STATUS_DELETED, bangumi_status=STATUS_UPDATING):
        join_cond = (Bangumi.name == cls.bangumi_name)
        d = cls.select(Bangumi.name, Bangumi.update_time, Bangumi.cover, cls, ) \
            .join(Bangumi, peewee.JOIN['LEFT_OUTER'], on=join_cond) \
            .where((cls.status != status) & (Bangumi.status == bangumi_status)) \
            .order_by(cls.updated_time.desc()) \
            .dicts()

        return list(d)


class Download(NeoDB):
    name = TextField(null=False)
    title = TextField(null=False)
    episode = IntegerField(default=0)
    download = TextField()
    status = IntegerField(default=0)

    @classmethod
    def get_all_downloads(cls, status=None):
        if status is None:
            data = list(cls.select().order_by(cls.status))
        else:
            data = list(cls.select().where(cls.status == status).order_by(cls.status))

        for index, x in enumerate(data):
            data[index] = model_to_dict(x)
        return data

    def downloaded(self):
        self.status = STATUS_DOWNLOADED
        self.save()


class Filter(NeoDB):
    bangumi_name = TextField(unique=True)
    subtitle = TextField(null=True)
    data_source = TextField(null=True)
    include = TextField(null=True)
    exclude = TextField(null=True)
    regex = TextField(null=True)


class Subtitle(NeoDB):
    id = TextField()
    name = TextField()
    data_source = TextField()

    class Meta:
        database = db
        indexes = (
            # create a unique on from/to/date
            (('id', 'data_source'), True),
        )

    @classmethod
    def get_subtitle_of_bangumi(cls, bangumi_obj):
        """

        :type bangumi_obj: Bangumi
        """
        return cls.get_subtitle_from_data_source_dict(bangumi_obj.data_source)

    @classmethod
    def get_subtitle_from_data_source_dict(cls, data_source):
        """
        :type data_source: dict
        :param data_source:
        :return:
        """
        source = list(data_source.keys())
        condition = list()
        for s in source:
            condition.append(
                (Subtitle.id.in_(data_source[s]['subtitle_group'])) & (Subtitle.data_source == s)
            )
        if len(condition) > 1:
            tmp_c = condition[0]
            for c in condition[1:]:
                tmp_c = tmp_c | c
        elif len(condition) == 1:
            tmp_c = condition[0]
        else:
            return []
        return [model_to_dict(x) for x in Subtitle.select().where(tmp_c)]


script_db = peewee.SqliteDatabase(bgmi.config.SCRIPT_DB_PATH)


class Scripts(peewee.Model):
    bangumi_name = TextField(null=False, unique=True)
    episode = IntegerField(default=0)
    status = IntegerField(default=0)
    updated_time = IntegerField(default=0)

    class Meta:
        database = script_db


def recreate_source_relatively_table():
    table_to_drop = [Bangumi, Followed, Subtitle, Filter, Download]
    for table in table_to_drop:
        table.delete().execute()
    return True


if __name__ == '__main__':  # pragma:no cover
    from pprint import pprint

    d = Bangumi.get(name='海贼王')
    d = (Subtitle.get_subtitle_of_bangumi(d))
    pprint(d)
