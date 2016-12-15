###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from __future__ import print_function
import gevent.monkey
import logging

gevent.monkey.patch_all()  # ensure the standard libraries are patched

# set configured registry
def _get_config():
  from . import config
  return config.view('phovea_server')

_log = logging.getLogger(__name__)

def enable_dev_mode():
  _log.info('enabling development mode')
  cc = _get_config()
  cc.set('env', 'development')
  cc.set('debug', True)
  cc.set('error_stack_trace', True)
  cc.set('nocache', True)

def enable_prod_mode():
  _log.info('enabling production mode')
  cc = _get_config()
  cc.set('env', 'production')
  cc.set('debug', False)
  cc.set('error_stack_trace', False)
  cc.set('nocache', False)

def _config_files():
  """
  list all known config files
  :return:
  """
  from .plugin import plugins
  return [p for p in (p.config_file() for p in plugins()) if p is not None]

def _resolve_launcher(launcher):
  """
  resolves the launcher if it is a string it will load the module and determine the function to use
  :param launcher:
  :return: launcher function
  """
  import six
  import os
  import importlib

  if isinstance(launcher, six.string_types):
    module_name, function_name = os.path.splitext(launcher)
    m = importlib.import_module(module_name)
    return m[function_name]

  return launcher

def run():
  import argparse
  from .plugin import list as list_plugins

  parser = argparse.ArgumentParser(description='Phovea Server')
  parser.add_argument('--use_reloader', action='store_true', help='whether to automatically reload the server')
  parser.add_argument('--env', default=cc.get('env'), help='environment mode (dev or prod)')

  commands = list_plugins('commands')
  subparsers = parser.add_subparsers(dest='cmd')
  for command in commands:
    cmdparser = parser if command.id == 'default' else subparsers.add_parser(command.id)
    instance = command.load().factory(cmdparser)
    cmdparser.setdefaults(launcher=instance)

  args = parser.parse_args()

  if args.env.startswith('dev'):
    enable_dev_mode()
  else:
    enable_prod_mode()

  main = args.launcher(args)

  if args.use_reloader:
    _log.info('start using reloader...')
    from werkzeug._reloader import run_with_reloader
    run_with_reloader(main, extra_files=_config_files())
  else:
    _log.info('start...')
    main()


def create_embedded():
  from .server import create_application
  return create_application()

if __name__ == '__main__':
  print('run as standalone version')
  run()
else:
  application = create_embedded()
  print('run as embedded version: %s', application)
