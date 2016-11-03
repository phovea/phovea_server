import flask
import os
import os.path
import caleydo_server.plugin
import caleydo_server.config

app = flask.Flask(__name__)

#deliver bower
@app.route('/bower_components/<path:path>')
def bowercomponents(path):
  return flask.send_from_directory(os.path.abspath(caleydo_server.config.get('bower_components','caleydo_server')), path)

#alternative name redirects
@app.route('/<string:app>/plugins/<path:path>')
def deliver_plugins(app, path):
  return flask.redirect('/' + path)

import re
black_list = re.compile(r'(.*\.(py|pyc|gitignore|gitattributes)|(\w+)/((config|package)\.json|_deploy/.*))')

def is_on_black_list(path):
  #print 'check',path,black_list.match(path) is not None
  return black_list.match(path) is not None

@app.route('/')
def index():
  return deliver('index.html')

@app.route('/<path:path>')
def deliver(path):
  #print path
  if path.endswith('/'):
    path += 'index.html'
  if is_on_black_list(path):
    return 'This page does not exist', 404

  for d in caleydo_server.config.getlist('pluginDirs','caleydo_server'):
    d = os.path.abspath(d)
    dpath = flask.safe_join(d, path)
    if os.path.exists(dpath):
      # send_static_file will guess the correct MIME type
      #print 'sending',dpath
      return flask.send_from_directory(d, path)
  return 'This page does not exist', 404

def default_app():
  return app
