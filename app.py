# app.py

from datetime import timedelta, datetime
import requests
import os

from celery import Celery
from celery.task import periodic_task

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery(__name__, broker=REDIS_URL)

APPS_TO_PING = [
    "immense-ridge-2398",
    "isitaleapyear",
    "isitonlineyet",
    "isitonspotify",
    "post-thing",
    "powerful-thicket-9270",
    "thereadinglist",
    "thesingleimg",
    "thewhiteboard",
    "thisisatasklog",
    "tweetboard",
]

URL_TO_POST = "http://thisisatasklog.herokuapp.com/api/"


def ping_url(url):
    resp = requests.get(url)
    return resp.status_code


@periodic_task(run_every=timedelta(minutes=1))
def log_ping():
    for app in APPS_TO_PING:
        url = "http://{app}.herokuapp.com/".format(app=app)
        payload = {
            "task": "{action} {url}".format(
                action="ping_url",
                url=url
            ),
            "result": ping_url(url),
            "time": datetime.now(),
        }
        log = requests.post(
            URL_TO_POST,
            data=payload
        )