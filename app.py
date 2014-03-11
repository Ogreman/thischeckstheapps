# app.py

import datetime, os

from flask import request, url_for, render_template

from flask.ext.api import FlaskAPI, status, exceptions
from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer
from flask.ext.api.exceptions import APIException
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import HSTORE


app = FlaskAPI(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)


class TaskHistory(db.Model):

    __tablename__ = "taskhistory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String)
    result = Column(MutableDict.as_mutable(HSTORE))

    def __repr__(self):
        return "Task history of task: {task}.".format(
            task=self.task,
        )

    def to_json(self):
        return {
            'id': self.id,
            'task': self.task,
            'result': self.result,
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