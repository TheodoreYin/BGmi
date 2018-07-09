# coding=utf-8
import sqlite3

from bgmi.config import SCRIPT_DB_PATH, BGMI_PATH
from bgmi.lib.models import Bangumi, Followed, Download, Filter, Subtitle
from bgmi.utils import print_error

CREATE_TABLE_SCRIPT = '''CREATE TABLE IF NOT EXISTS scripts (
          id INTEGER PRIMARY KEY  AUTOINCREMENT,
          bangumi_name TEXT UNIQUE NOT NULL,
          episode INTEGER DEFAULT 0,
          status INTEGER DEFAULT 1,
          updated_time INTEGER DEFAULT 0
        )'''

CLEAR_TABLE_ = 'DELETE  FROM {}'


def init_db():
    try:
        # bangumi.db
        # conn = sqlite3.connect(DB_PATH)
        for x in [Bangumi, Followed, Download, Filter, Subtitle]:
            x.create_table()
        # conn.commit()
        # conn.close()

        # script.db
        conn = sqlite3.connect(SCRIPT_DB_PATH)
        conn.execute(CREATE_TABLE_SCRIPT)
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        print_error('Open database file failed, path %s is not writable.' % BGMI_PATH)
