# app.py

from datetime import timedelta, datetime, date

import requests
from requests.auth import HTTPBasicAuth
import os
import sys
import heroku

from celery import Celery
from celery.task import periodic_task
from celery.schedules import crontab

from twilio.rest import TwilioRestClient


REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery(__name__, broker=REDIS_URL)

task_log_url = "http://thisisatasklog.herokuapp.com/api/"
tweet_url = "http://tweetboard.herokuapp.com/api/"
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S +0000"
SPOTIFY_URL = "http://isitonspotify.herokuapp.com/api?artist={artist}"

TASKS = {}


@periodic_task(run_every=timedelta(hours=2))
def check_toggles():        
    auth = HTTPBasicAuth(os.environ['TOGGLE_NAME'], os.environ['TOGGLE_PASS'])
    response = requests.get('http://thistogglesthetasks.herokuapp.com/tasks/', auth=auth)
    if response.ok:
        results = response.json()['results'] 
        TASKS.update(
            { 
                task['name']: task['active']
                for task in results
            }
        )


def log_this(task, target, result):
    payload = {
        "task": task,
        "target": target,
        "result": result,
        "time": datetime.now(),
    }
    resp = requests.post(
        task_log_url,
        data=payload
    )
    print resp.content


@periodic_task(run_every=timedelta(hours=3))
def log_ping():
    if TASKS.get('log_ping'):
        heroku_user = os.environ['HEROKU_USERNAME']
        heroku_pass = os.environ['HEROKU_PASSWORD']
        cloud = heroku.from_pass(heroku_user, heroku_pass)
        for app in (h_app.name for h_app in cloud.apps):
            url = "http://{app}.herokuapp.com/".format(app=app)
            result = requests.get(url).status_code
            log_this(sys._getframe().f_code.co_name, url, result)


@periodic_task(run_every=timedelta(hours=24))
def tweet_check():
    if TASKS.get('tweet_check'):    
        get_url = "http://tweetboard.herokuapp.com/api/recent/"
        response = requests.get(get_url)
        if response.ok:
            posts = response.json()
            if posts:
                tweet = "Posted {n} new anonymous {tweets} today.".format(
                    n=len(posts),
                    tweets="tweets" if len(posts) > 1 else "tweet" 
                )
                requests.post(tweet_url, data={'text': tweet})
        log_this(sys._getframe().f_code.co_name, get_url, response.status_code)


@periodic_task(run_every=crontab(day_of_month='1', month_of_year='1'))
def leap_tweet():
    if TASKS.get('leap_tweet'):    
        get_url = "http://isitaleapyear.herokuapp.com/api/?year={year}".format(
            year=datetime.now().year
        )
        response = requests.get(get_url)
        if response.ok:
            leap = response.json()
            tweet = "Happ New Year! {year} {leap} a leap year.".format(
                year=leap['year'],
                leap="is" if leap['leap'] else "is not",
            )
            requests.post(tweet_url, data={'text': tweet})
        log_this(sys._getframe().f_code.co_name, get_url, response.status_code)


@periodic_task(run_every=timedelta(hours=1))
def check_sms():
    if TASKS.get('check_sms'):    
        account = os.environ['TWILIO_ACCOUNT_SID']
        auth = os.environ['TWILIO_AUTH_TOKEN']
        me = os.environ['MY_NUMBER']
        today = date.today() 
        now = datetime.now()
        client = TwilioRestClient(account, auth)
        messages = client.messages.list(
            from_=me,
            date_sent=str(today)
        )
        if messages:
            text = messages[0]
            text_dt = datetime.strptime(text.date_sent, DATE_FORMAT)
            if now - text_dt < timedelta(hours=1): 
                if "SPOTIFY" in text.body:
                    artist = text.body.replace("SPOTIFY", "")
                    result = requests.get(SPOTIFY_URL.format(artist=artist))
                    client.messages.create(
                        body="{artist} is {on} spotify".format(
                            artist=artist,
                            on="on" if result.json()['check'] else "not on"
                        ),
                        to=text.from_,
                        from_=text.to,
                    )
                else:
                    requests.post(tweet_url, data={'text': text.body})
                status = 1
            else:
                status = 0
        else:
            status = -1
        log_this(sys._getframe().f_code.co_name, "SMS", status)
