import datetime
import os
import re
import string
from collections import defaultdict
from copy import deepcopy
from typing import List, Dict

import requests
from fuzzywuzzy import fuzz
from hanziconv import HanziConv

from bgmi.lib import models
from bgmi.lib.constants import (SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS)
from bgmi.website import DATA_SOURCE_MAP, init_data
from bgmi.lib.models import Bangumi, STATUS_UPDATED, STATUS_FOLLOWED
from bgmi.utils import (print_warning, GREEN, YELLOW, COLOR_END, get_terminal_col)

from bgmi.website import DataSource

from bgmi.lib import models

models.Bangumi.create_table()
models.Followed.create_table()
models.Subtitle.create_table()


def cal_wrapper():
    weekly_list = DataSource().bangumi_calendar(force_update=True)

    def shift(seq, n):
        n %= len(seq)
        return seq[n:] + seq[:n]

    today = False
    weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    env_columns = 42 if os.environ.get('TRAVIS_CI', False) else get_terminal_col()

    col = 42

    if env_columns < col:
        print_warning('terminal window is too small.')
        env_columns = col

    row = int(env_columns / col if env_columns / col <= 3 else 3)

    def print_line():
        num = col - 3
        split = '-' * num + '   '
        print(split * row)

    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            print(
                '%s%s. %s' % (
                    GREEN, weekday if not today else 'Bangumi Schedule for Today (%s)' % weekday, COLOR_END),
                end='')
            print()
            print_line()
            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if bangumi['status'] in (STATUS_UPDATED, STATUS_FOLLOWED) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (
                        bangumi['name'], bangumi['episode'])

                half = len(re.findall('[%s]' %
                                      string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half)
                space_count = col - 2 - (full * 2 + half)

                for s in SPACIAL_APPEND_CHARS:
                    if s in bangumi['name']:
                        space_count += bangumi['name'].count(s)

                for s in SPACIAL_REMOVE_CHARS:
                    if s in bangumi['name']:
                        space_count -= bangumi['name'].count(s)

                if bangumi['status'] == STATUS_FOLLOWED:
                    bangumi['name'] = '%s%s%s' % (
                        YELLOW, bangumi['name'], COLOR_END)

                if bangumi['status'] == STATUS_UPDATED:
                    bangumi['name'] = '%s%s%s' % (
                        GREEN, bangumi['name'], COLOR_END)
                try:
                    print(' ' + bangumi['name'], ' ' * space_count, end='')
                except UnicodeEncodeError:
                    continue

                if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                    print()
            print()


cal_wrapper()
