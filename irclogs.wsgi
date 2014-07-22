import sys
import os
import logging

logging.basicConfig(stream=sys.stderr)

thisdir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, thisdir)

from app import app as flask_app

def application(environ, start_response):
   for key, value in environ.items():
      if type(key) != str or type(value) != str:
         continue
      os.environ[key] = value
   return flask_app(environ, start_response)
