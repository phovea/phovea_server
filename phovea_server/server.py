###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from __future__ import absolute_import
import gevent.monkey
import logging.config


gevent.monkey.patch_all()  # ensure the standard libraries are patched


# set configured registry
def _get_config():
  from . import config
  return config.view('phovea_server')


# append the plugin directories as primary lookup path
cc = _get_config()
# configure logging
logging.config.dictConfig(cc.logging)
_log = logging.getLogger(__name__)


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


def _rest_cache(namespace):
  import os
  from os import path
  import hashlib
  from werkzeug import url_quote

  dir_name = path.join(cc.restCacheDir, namespace[1:])
  if not path.exists(dir_name):
    os.makedirs(dir_name)

  def to_filename(request):
    secure = url_quote(request.full_path[1:].replace('/', ' ').replace('?', '_').replace('=', '-').replace('&', '_'), safe=' ')
    key = hashlib.sha256(namespace + secure).hexdigest()
    file_name = '{}_{}.json'.format(secure[:min(128, len(secure))], key)
    return file_name.replace('%', '_')

  def save(response):
    from flask import request

    if request.method != 'GET' or response.status_code != 200 or response.mimetype != 'application/json' or response.is_streamed or response.cache_control.no_cache:
      return response

    file_name = to_filename(request)
    _log.info('cache %s %s -> %s %s', namespace, request.full_path, dir_name, file_name)

    with open(path.join(dir_name, file_name), 'w') as f:
      f.write(response.get_data())

    # print(response.mimetype, data)
    return response

  def load():
    from flask import request, send_from_directory
    file_name = to_filename(request)

    full = path.join(dir_name, file_name)

    if path.exists(full):
      _log.info('use cache cache %s %s <- %s', namespace, request.full_path, full)
      return send_from_directory(path.abspath(dir_name), file_name, add_etags=False)
    return None

  return save, load


def _to_stack_trace():
  import traceback
  return traceback.format_exc()


def _exception_handler(error):
  return 'Internal Server Error\n' + _to_stack_trace(), 500


def _init_app(app, namespace, is_default_app=False):
  """
  initializes an application by setting common properties and options
  :param app:
  :param is_default_app:
  :return:
  """
  from . import security

  if hasattr(app, 'got_first_request') and app.got_first_request:
    _log.warn('already inited: ' + str(app))
    return

  _log.info('init application: ' + str(app))

  if hasattr(app, 'debug'):
    app.debug = cc.debug
  if cc.nocache and hasattr(app, 'after_request'):
    app.after_request(_add_no_cache_header)
  if cc.error_stack_trace and hasattr(app, 'register_error_handler'):
    app.register_error_handler(500, _exception_handler)

  if cc['restCache'] == 'record' and hasattr(app, 'after_request'):
    app.after_request(_rest_cache(namespace)[0])
  if cc['restCache'] is True and hasattr(app, 'before_request'):
    app.before_request(_rest_cache(namespace)[1])

  if cc.secret_key:
    app.config['SECRET_KEY'] = cc.secret_key

  if cc.max_file_size:
    app.config['MAX_CONTENT_LENGTH'] = cc.max_file_size

  security.init_app(app)
  if is_default_app:
    security.add_login_routes(app)


# helper to plugin in function scope
def _loader(p):
  print('add application: ' + p.id + ' at namespace: ' + p.namespace)

  def load_app():
    app = p.load().factory()
    _init_app(app, p.namespace)
    return app

  return load_app


def _pre_load_caches():
  """
  preload some manager to start them up
  :return:
  """
  c = _get_config().coldstart

  if c['assigner']:
    from .dataset import get_idmanager
    _log.info('initialize id assigner')
    get_idmanager()

  if c['mapping']:
    from .dataset import get_mappingmanager
    _log.info('initialize mapping manager')
    get_mappingmanager()


def create_application():
  from . import dispatcher
  from . import mainapp
  from .plugin import list as list_plugins
  from werkzeug.contrib.fixers import ProxyFix

  # create a path dispatcher
  _default_app = mainapp.default_app()
  _init_app(_default_app, '/', True)
  _applications = {p.namespace: _loader(p) for p in list_plugins('namespace')}

  # create a dispatcher for all the applications
  application = dispatcher.PathDispatcher(_default_app, _applications)

  _pre_load_caches()

  return ProxyFix(application)


def create(parser):
  parser.add_argument('--port', '-p', type=int, default=cc.getint('port'),
                      help='server port')
  parser.add_argument('--address', '-a', default=cc.get('address'),
                      help='server address')

  def _launcher(args):
    from geventwebsocket.handler import WebSocketHandler
    from gevent.pywsgi import WSGIServer
    application = create_application()
    http_server = WSGIServer((args.address, args.port), application, handler_class=WebSocketHandler)

    return http_server.serve_forever

  return _launcher
