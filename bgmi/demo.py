import json

import requests

from bgmi.website import init_data, DATA_SOURCE_MAP
from bgmi.lib.models import TYPE_MAINLINE, STATUS_UPDATING, TYPE_LEFT

d = {}
for key, value in DATA_SOURCE_MAP.items():
    b, s = value.fetch_bangumi_calendar_and_subtitle_group()
    for bgm in b:
        bgm['type'] = TYPE_LEFT
        bgm['cover'] = value.cover_url + bgm['cover']
        bgm['data_source'] = {}
    d[key] = b[:5]

r = requests.get('https://api.bgm.tv/calendar')
r = r.json()
bangumi_tv_weekly_list = []

for day in r:
    for index, item in enumerate(day['items']):
        day['items'][index] = {
            'name'       : item['name_cn'],
            'update_time': day['weekday']['en'].capitalize(),
            'keyword'    : item['id'],
            "status"     : STATUS_UPDATING,
            "cover"      : item.get('images', {}),
            "type"       : TYPE_MAINLINE,
            'data_source': {},
        }
    bangumi_tv_weekly_list += day['items']
d['bangumi_tv'] = bangumi_tv_weekly_list[:5]

# d = init_data()
with open('tmp/bangumi.json', 'w+', encoding='utf8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
# with open('tmp/subtitle.json', 'w+', encoding='utf8') as f:
#     json.dump(d[1], f, ensure_ascii=False, indent=2)
