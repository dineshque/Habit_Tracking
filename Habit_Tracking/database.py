# -*- coding: utf-8 -*-
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
app=current_app
db=SQLAlchemy(app)
db.init_app(app)

class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String,nullable=False,unique=True)
    password=db.Column(db.String,nullable=False)
    trackers=db.relationship("tracker",cascade='all',backref="parent")

class tracker(db.Model):
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    tracker_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(30),nullable=False)
    desc=db.Column(db.String)
    type=db.Column(db.String,nullable=False)
    settings=db.Column(db.String)
    lastupdate=db.Column(db.DateTime)
    logs=db.relationship("log",cascade='all', backref="parent")

class log(db.Model):
    tracker_id=db.Column(db.Integer,db.ForeignKey("tracker.tracker_id"),nullable=False)
    log_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    log_datetime=db.Column(db.DateTime,nullable=False)
    note=db.Column(db.String)
    log_value=db.Column(db.String,nullable=False)
