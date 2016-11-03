from phovea_server import ns
import os
import os.path
import phovea_server.plugin
import phovea_server.config

app = ns.Namespace(__name__)

#deliver bower
@app.route('/bower_components/<path:path>')
def bowercomponents(path):
  return ns.send_from_directory(os.path.abspath(phovea_server.config.get('bower_components','phovea_server')), path)

#alternative name redirects
@app.route('/<string:app>/plugins/<path:path>')
def deliver_plugins(app, path):
  return ns.redirect('/' + path)

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

  for d in phovea_server.config.getlist('pluginDirs','phovea_server'):
    d = os.path.abspath(d)
    dpath = ns.safe_join(d, path)
    if os.path.exists(dpath):
      # send_static_file will guess the correct MIME type
      #print 'sending',dpath
      return ns.send_from_directory(d, path)
  return 'This page does not exist', 404

def default_app():
  return app
