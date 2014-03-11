# app.py

from datetime import timedelta, datetime
import requests
import os

from celery import Celery
from celery.task import periodic_task

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery(__name__, broker=REDIS_URL)

APPS_TO_PING = [
    "http://isitaleapyear.herokuapp.com/",
    "http://thisisatasklog.herokuapp.com/",
]

URL_TO_POST = "http://thisisatasklog.herokuapp.com/api/"


def ping_url(url):
    resp = requests.get(url)
    return resp.status_code


@periodic_task(run_every=timedelta(minutes=1))
def log_ping():
    for url in APPS_TO_PING:
        payload = {
            "title": "{action} {url}".format(
                action="log_ping",
                url=url
            ),
            "result": ping_url(url),
            "time": datetime.now(),
        }
        log = request.post(
            URL_TO_POST,
            data=payload
        )