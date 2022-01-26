###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

import logging.config
import threading
import time


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
    file_name_old = '{}_{}.json'.format(secure[:min(128, len(secure))], key)
    file_name = '{}_{}.json'.format(secure[:min(64, len(secure))], key)  # use a shorter filename for restCache, to avoid file system errors with too long file names
    return {
      "file_name_128": file_name_old.replace('%', '_'),  # file_name_128 = file name with 128 characters in front of the hash
      "file_name_64": file_name.replace('%', '_')  # file_name_64 = file name with 64 characters in front of the hash
    }

  def save(response):
    from flask import request

    if request.method != 'GET' or response.status_code != 200 or response.mimetype != 'application/json' or response.is_streamed or response.cache_control.no_cache:
      return response

    file_name = to_filename(request)['file_name_64']  # only use the short file name for storing new files

    _log.info('cache %s %s -> %s %s', namespace, request.full_path, dir_name, file_name)

    with open(path.join(dir_name, file_name), 'w') as f:
      f.write(response.get_data())

    # print(response.mimetype, data)
    return response

  def load():
    from flask import request, send_from_directory

    file_names = to_filename(request)

    # use the legacy file name ('file_name_128') if a file with this name exists and the new file name format otherwise
    file_name = file_names['file_name_128'] if path.exists(file_names['file_name_128']) else file_names['file_name_64']

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
  _log.info('add application: ' + p.id + ' at namespace: ' + p.namespace)

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

  if c['mapping']:
    from .dataset import get_mappingmanager
    _log.info('initialize mapping manager')
    get_mappingmanager()


def create_application():
  from . import dispatcher
  from . import mainapp
  from .plugin import list as list_plugins
  from werkzeug.middleware.proxy_fix import ProxyFix

  # create a path dispatcher
  _default_app = mainapp.default_app()
  _init_app(_default_app, '/', True)
  _applications = {p.namespace: _loader(p) for p in list_plugins('namespace')}

  # create a dispatcher for all the applications
  application = dispatcher.PathDispatcher(_default_app, _applications)

  _pre_load_caches()

  return ProxyFix(application)


def create(parser):
  """
  Add arguments to the parser and return a launcher function, which in-turn creates a server instance
  parser: ArgumentParser that allows to add custom arguments. The arguments will be passed as parameter to the launcher function.
  """
  parser.add_argument('--port', '-p', type=int, default=cc.getint('port'),  # get default value from config.json
                      help='server port')
  parser.add_argument('--address', '-a', default=cc.get('address'),  # get default value from config.json
                      help='server address')
  parser.add_argument('--certfile', '-c', default=cc.get('certfile'),  # get default value from config.json
                      help='ssl certificate')
  parser.add_argument('--keyfile', '-k', default=cc.get('keyfile'),  # get default value from config.json
                      help='keyfile for ssl certificate')

  def _launcher(args):
    """
    Prepare the launch of the server instance
    args: contains the arguments that are parsed from the command line (or set in the config as default value)
    """
    from geventwebsocket.handler import WebSocketHandler
    from gevent.pywsgi import WSGIServer
    from flask.logging import default_handler
    import logging
    # from gevent import monkey

    # create phovea server application
    application = create_application()

    # add handler for wsgi's logger
    logger = logging.getLogger('wsgi')
    logger.setLevel(logging.INFO)
    _log.addHandler(default_handler)

    _log.info('prepare server that will listen on %s:%s [cert=%s, key=%s]', args.address, args.port, args.certfile, args.keyfile)
    # Test whether monkey.patch_all() has been used correctly,
    # keys have to be set
    # _log.warn(monkey.saved.keys())
    if args.certfile and args.keyfile:
      http_server = WSGIServer((args.address, args.port), application, keyfile=args.keyfile, certfile=args.certfile, handler_class=WebSocketHandler)
    else:
      http_server = WSGIServer((args.address, args.port), application, handler_class=WebSocketHandler)

    server = http_server.serve_forever  # return function name only; initialization will be done later

    # load `after_server_started` extension points which are run immediately after server started,
    # so all plugins should have been loaded at this point of time
    # the hooks are run in a separate (single) thread to not block the main execution of the server
    t = threading.Thread(target=_load_after_server_started_hooks)
    t.setDaemon(True)
    t.start()

    return server

  return _launcher


def _load_after_server_started_hooks():
  """
    Load and run all `after_server_started` extension points.
    The factory method of an extension implementing this extension point should return a function which is then executed here
  """
  from .plugin import list as list_plugins

  start = time.time()

  after_server_started_hooks = [p.load().factory() for p in list_plugins('after_server_started')]

  _log.info("Found %d `after_server_started` extension points to run", len(after_server_started_hooks))

  for hook in after_server_started_hooks:
    hook()

  _log.info("Elapsed time for server startup hooks: %d seconds", time.time() - start)
