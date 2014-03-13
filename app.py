# app.py

from datetime import timedelta, datetime

import requests
import os
import sys
import heroku

from celery import Celery
from celery.task import periodic_task


REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery(__name__, broker=REDIS_URL)

task_log_url = "http://thisisatasklog.herokuapp.com/api/"


def ping_url(url):
    resp = requests.get(url)
    return resp.status_code


@periodic_task(run_every=timedelta(hours=3))
def log_ping():
    heroku_user = os.environ['HEROKU_USERNAME']
    heroku_pass = os.environ['HEROKU_PASSWORD']
    cloud = heroku.from_pass(heroku_user, heroku_pass)
    for app in (h_app.name for h_app in cloud.apps):
        url = "http://{app}.herokuapp.com/".format(app=app)
        payload = {
            "task": sys._getframe().f_code.co_name,
            "target": url,
            "result": ping_url(url),
            "time": datetime.now(),
        }
        log = requests.post(
            task_log_url,
            data=payload
        )


@periodic_task(run_every=timedelta(hours=24))
def tweet_check():
    get_url = "http://tweetboard.herokuapp.com/api/recent/"
    post_url = "http://tweetboard.herokuapp.com/api/"
    response = requests.get(get_url)
    if response.ok:
        posts = response.json()
        if posts:
            tweet = "There were {n} new anonymous tweets today.".format(
                n=len(posts)
            )
            requests.post(post_url, data={ 'text': tweet })
    payload = {
        "task": sys._getframe().f_code.co_name,
        "target": get_url,
        "result": response.status_code,
        "time": datetime.now(),
    }
    log = requests.post(
        task_log_url,
        data=payload
    )