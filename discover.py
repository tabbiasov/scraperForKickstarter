import time
import logging
import requests
from conf import *

def url(p):
    return "https://www.kickstarter.com/discover/recently-launched?page=" + str(p) + "&seed="

hdr = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4",
    "X-Requested-With": "XMLHttpRequest",
}

def discover_projects():

    db.connect()

    new = True
    p = 1
    session_buffer = set()

    while new:
        i = 0
        data = requests.get(url(p), headers=hdr).json()['projects']
        while new & (i < len(data)):
            if not(data[i]['id'] in session_buffer):
                session_buffer.add(data[i]['id'])
                try:
                    Projects.create(id=data[i]['id'],
                                    name=data[i]['name'],
                                    goal=data[i]['goal'],
                                    currency=data[i]['currency'],
                                    country=data[i]['country'],
                                    created_at=data[i]['created_at'],
                                    launched_at=data[i]['launched_at'],
                                    deadline=data[i]['deadline'],
                                    parent_category=data[i]['category'].get('parent_id', data[i]['category'].get('id')),
                                    location_woeid=data[i]['location']['id'],
                                    creator_id=data[i]['creator']['id'],
                                    disable_communication=data[i]['disable_communication'],
                                    currency_trailing_code=data[i]['currency_trailing_code'])
                except IntegrityError:
                    new = False
            i += 1
        p += 1

def renew_records():

    db.connect()

    end_not_reached = True
    p = 1
    delay = 360
    end_id = Projects\
        .select()\
        .where(Projects.deadline >= time.time()-delay)\
        .order_by(Projects.launched_at.asc())\
        .first()\
        .id
    session_buffer = set()

    while end_not_reached:
        i = 0
        data = requests.get(url(p), headers=hdr).json()['projects']
        while end_not_reached & (i < len(data)):
            curr_id = data[i]['id']
            if not(curr_id in session_buffer):
                session_buffer.add(curr_id)
                try:
                    Snapshots.create(timestamp=int(time.time()),
                                     id=curr_id,
                                     pledged=data[i]['pledged'],
                                     backers_count=data[i]['backers_count'],
                                     status=data[i]['state'][0].upper())
                except Projects.DoesNotExist:
                    logging.warning('Project ' + str(curr_id) + ' is not in the projects list!')
            i += 1
            if curr_id == end_id:
                end_not_reached = False
        p += 1

