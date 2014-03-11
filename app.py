# app.py

from datetime import timedelta, datetime
import requests
import os

from flask import request, url_for, render_template

from flask.ext.api import FlaskAPI, status, exceptions
from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer
from flask.ext.api.exceptions import APIException
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import Column, String, Integer, DateTime

from celery import Celery
from celery.task import periodic_task

app = FlaskAPI(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'],
)
db = SQLAlchemy(app)

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost')
celery = Celery('tasks', broker=REDIS_URL)

APPS_TO_PING = [
    "http://isitaleapyear.herokuapp.com/",
]


def ping_url(url):
    resp = requests.get(url)
    return resp.status_code


@periodic_task(run_every=timedelta(minutes=1))
def log_ping():
    for url in APPS_TO_PING:
        log = TaskHistory(
            title="{action} {url}".format(action="log_ping", url=url),
            result=ping_url(url),
            time=datetime.now(),
        )
        db.session.add(log)
    db.session.commit()


class TaskHistory(db.Model):

    __tablename__ = "taskhistory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String)
    result = Column(Integer)
    time = Column(DateTime)

    def __repr__(self):
        return "Task history of task: {task}.".format(
            task=self.task,
        )

    def to_json(self):
        return {
            'id': self.id,
            'task': self.task,
            'result': self.result,
            'tiime': self.time,
        }

    @classmethod
    def get_tasks(self):
        return [
            log.to_json() for log in TaskHistory.query.all()
        ]


@app.route("/api/", methods=['GET'])
def logs():
    """
    List or create logs.
    """
    return TaskHistory.get_tasks(), status.HTTP_200_OK


if __name__ == "__main__":
    app.run(debug=True)