# app.py

from datetime import timedelta, datetime

import requests
import os
import heroku

from celery import Celery
from celery.task import periodic_task

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery(__name__, broker=REDIS_URL)

HEROKU_USER = os.environ['HEROKU_USERNAME']
HEROKU_PASS = os.environ['HEROKU_PASSWORD']
cloud = heroku.from_pass(HEROKU_USER, HEROKU_PASS)
APPS_TO_PING = [
    app.name for app in cloud.apps
]

URL_TO_POST = "http://thisisatasklog.herokuapp.com/api/"


def ping_url(url):
    resp = requests.get(url)
    return resp.status_code


@periodic_task(run_every=timedelta(minutes=15))
def log_ping():
    for app in APPS_TO_PING:
        url = "http://{app}.herokuapp.com/".format(app=app)
        payload = {
            "task": "ping_url",
            "target": url,
            "result": ping_url(url),
            "time": datetime.now(),
        }
        log = requests.post(
            URL_TO_POST,
            data=payload
        )