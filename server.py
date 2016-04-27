__author__ = 'Samuel Gratzl'

import gevent.monkey
gevent.monkey.patch_all() #ensure the standard libraries are patched

import os.path
import sys


sys.path.append('plugins/')
import caleydo_server.config

#append the plugin directories as primary lookup path
cc = caleydo_server.config.view('caleydo_server')

#configure logging
import logging.config

logging.config.dictConfig(cc.logging)

_log = logging.getLogger(__name__)
_log.debug('extent with plugin directory %s',str(cc.getlist('pluginDirs')))

sys.path.extend(cc.getlist('pluginDirs'))

#set configured registry
import caleydo_server.plugin

import dispatcher
import mainapp

def _add_no_cache_header(response):
  """
  disable caching on the response
  :param response:
  :return:
  """
  #  response.headers['Last-Modified'] = datetime.now()
  response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '-1'
  return response

def _init_app(app, is_default_app = False):
  """
  initializes an application by setting common properties and options
  :param app:
  :param is_default_app:
  :return:
  """
  if hasattr(app, 'debug'):
    app.debug = cc.debug
  if cc.nocache and hasattr(app, 'after_request'):
    app.after_request(_add_no_cache_header)
  if cc.secret_key:
    app.config['SECRET_KEY'] = cc.secret_key

  if cc.max_file_size:
    app.config['MAX_CONTENT_LENGTH'] = cc.max_file_size

  import caleydo_server.security
  caleydo_server.security.init_app(app)
  if is_default_app:
    caleydo_server.security.add_login_routes(app)

#helper to plugin in function scope
def _loader(p):
  _log.info('add application: ' + p.id + ' at namespace: ' + p.namespace)
  def load_app():
    app = p.load().factory()
    _init_app(app)
    return app
  return load_app

#create a path dispatcher
_default_app = mainapp.default_app()
_init_app(_default_app, True)
_applications = { p.namespace : _loader(p) for p in caleydo_server.plugin.list('namespace') }

#create a dispatcher for all the applications
application = dispatcher.PathDispatcher(_default_app, _applications)
from werkzeug.contrib.fixers import ProxyFix

#the public wsgi application
application = ProxyFix(application)

def run():
  import argparse
  parser = argparse.ArgumentParser(description='Caleydo Web Server')
  parser.add_argument('--port', '-p', type=int, default=caleydo_server.config.getint('port','caleydo_server'), help='server port')
  parser.add_argument('--address', '-a', default=caleydo_server.config.get('address','caleydo_server'), help='server address')
  parser.add_argument('--use_reloader', action='store_true', help='whether to automatically reload the server')
  args = parser.parse_args()

  from geventwebsocket.handler import WebSocketHandler
  from gevent.pywsgi import WSGIServer

  http_server = WSGIServer((args.address, args.port), application, handler_class=WebSocketHandler)
  http_server.serve_forever()

  #from werkzeug.serving import run_simple
  #run_simple(args.address, args.port, application, use_reloader=args.use_reloader or caleydo_server.config.getboolean('use_reloader','caleydo_server'))
