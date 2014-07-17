from flask import Flask, redirect, url_for, abort, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template

from sqlalchemy import func, distinct, desc, select

from sqlalchemy.ext.hybrid import hybrid_property

#from flask.ext.security import Security, SQLAlchemyUserDatastore, \
#    UserMixin, RoleMixin, login_required

from itertools import groupby
import bleach
import datetime

from os import environ as env


# Models

#roles_users = db.Table('roles_users',
#        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
#        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))
#
#class Role(db.Model, RoleMixin):
#    id = db.Column(db.Integer(), primary_key=True)
#    name = db.Column(db.String(80), unique=True)
#    description = db.Column(db.String(255))
#
#class User(db.Model, UserMixin):
#    id = db.Column(db.Integer, primary_key=True)
#    email = db.Column(db.String(255), unique=True)
#    password = db.Column(db.String(255))
#    active = db.Column(db.Boolean())
#    confirmed_at = db.Column(db.DateTime())
#    roles = db.relationship('Role', secondary=roles_users,
#                            backref=db.backref('users', lazy='dynamic'))

app = Flask(__name__)
db = SQLAlchemy(app)

@app.before_first_request
def setup():
   global app

   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s/IrcLogs' % (
      env['LOGS_USERNAME'],
      env['LOGS_PASSWORD'],
      env['LOGS_HOSTNAME'],
   )

   app.config['SQLALCHEMY_ECHO'] = True
   app.config['SECRET_KEY'] = env['LOGS_SECRET_KEY']

class Entry(db.Model):
   __tablename__ = 'ab_logs'
   id = db.Column(db.Integer, primary_key=True)
   kind = db.Column(db.String(80))
   who = db.Column(db.String(120))
   when = db.Column(db.DateTime())
   msg = db.Column(db.String(120))
   bot_speak = db.Column(db.Boolean)
   channel = db.Column(db.String(120))

   @hybrid_property
   def time(self):
      return self.when.strftime('%I:%M %p')

def next_day(date):
   return date + datetime.timedelta(days=1)

def format_date(date):
   return date.strftime('%Y-%m-%d')


def hfMonth(month):
   return (
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December'
   )[int(month)-1]

def hfDate(dateArr):
   year, month, date = [int(x) for x in dateArr]
   month = hfMonth(month)
   return "%s %s, %s" % (month, date, year)

# Setup Flask-Security
# user_datastore = SQLAlchemyUserDatastore(db, User, Role)
# security = Security(app, user_datastore)

@app.route('/')
@app.route('/irc/')
#@login_required
def index():
   return redirect(url_for('logs'))

@app.route('/irc/logs/')
def logs():
   return redirect(url_for('channel', channel='starryexpanse'))

@app.route('/irc/logs/<channel>/')
def channel(channel):
   dates = db.session.query(
      distinct(func.date(Entry.when)).label('d')
   ).filter(Entry.channel == '#'+channel).order_by(desc('d'))

   dates = [[int(x) for x in str(date[0]).split('-')] for date in dates]

   fdates = []
   for year, yeardates in groupby(dates, lambda d: d[0]):
      months = []
      for month, monthdates in groupby(yeardates, lambda y: y[1]):
         months.append({
            'month': hfMonth(month),
            'dates': [{
                  'date': hfDate(x),
                  'url': url_for('day', channel=channel, year=year, month=month, day=x[2])
               } for x in monthdates]
         })
      fdates.append({
         'year': year,
         'months': months
      })
      
   return render_template('channel.html', channel=channel, dates=fdates)

@app.route('/irc/logs/<channel>/<int:year>/<int:month>/<int:day>/')
def day(channel, year, month, day):
   date = datetime.date(year, month, day)
   entries = Entry.query.filter(
         Entry.channel == '#' + channel,
         Entry.when >= format_date(date) + ' 00:00:00',
         Entry.when < format_date(next_day(date)) + ' 00:00:00',
      ).order_by(Entry.when)

   return render_template('logs.html', entries=entries)

@app.route('/irc/logs/<int:year>/<int:month>/<int:day>/')
def day_backwards_compatibility(year, month, day):
   return redirect(url_for('day', channel='starryexpanse', year=year, month=month, day=day), 301)

if __name__ == '__main__':
   app.debug=True
   app.run(host='0.0.0.0', debug=True)
