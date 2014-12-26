from flask import Flask, redirect, url_for, abort, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template

from sqlalchemy import func, distinct, desc, select

from sqlalchemy.ext.hybrid import hybrid_property

from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

from itertools import groupby
import bleach
import datetime

from bs4 import BeautifulSoup

from os import environ as env

app = Flask(__name__)
db = SQLAlchemy(app)


@app.before_first_request
def setup():
   global app
   app.config['DEBUG'] = True
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s/IrcLogs' % (
      env['LOGS_USERNAME'],
      env['LOGS_PASSWORD'],
      env['LOGS_HOSTNAME'],
   )
   
   app.config['SQLALCHEMY_ECHO'] = True
   app.config['SECRET_KEY'] = env['LOGS_SECRET_KEY']


@app.template_filter('add_anchor_last_row')
def add_anchor_last_row(s):
   s = unicode(s)
   soup = BeautifulSoup(s, 'html.parser')

   alltrs = soup.find_all('tr')
   if len(alltrs) == 0:
      return s
   tds = alltrs[-1].find_all('td')
   index = -2
   if len(tds) < 2:
      index = -1
   td = tds[index]
   a = soup.new_tag('a')
   a['name'] = 'last'
   for content in list(td.contents):
      a.append(content)
   td.clear()
   td.append(a)

   return unicode(soup)

   #return s[::-1]

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

@app.route('/')
@app.route('/irc/')
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
