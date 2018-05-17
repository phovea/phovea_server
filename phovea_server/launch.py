###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from __future__ import print_function
import logging.config


# set configured registry
def _get_config():
  from . import config
  return config.view('phovea_server')


cc = _get_config()
_log = logging.getLogger(__name__)


def enable_dev_mode():
  _log.info('enabling development mode')
  cc.set('env', 'development')
  cc.set('debug', True)
  cc.set('error_stack_trace', True)
  cc.set('nocache', False)


def enable_prod_mode():
  _log.info('enabling production mode')
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


def set_default_subparser(parser, name, args=None):
  """default subparser selection. Call after setup, just before parse_args()
  name: is the name of the subparser to call by default
  args: if set is the argument list handed to parse_args()
  see http://stackoverflow.com/questions/5176691/argparse-how-to-specify-a-default-subcommand

  , tested with 2.7, 3.2, 3.3, 3.4
  it works with 2.6 assuming argparse is installed
  """
  import sys
  import argparse

  subparser_found = False
  for arg in sys.argv[1:]:
    if arg in ['-h', '--help']:  # global help if no subparser
      break
  else:
    for x in parser._subparsers._actions:
      if not isinstance(x, argparse._SubParsersAction):
        continue
      for sp_name in x._name_parser_map.keys():
        if sp_name in sys.argv[1:]:
          subparser_found = True
    if not subparser_found:
      # insert default in first position, this implies no
      # global options without a sub_parsers specified
      if args is None:
        sys.argv.insert(1, name)
      else:
        args.insert(0, name)


def _resolve_commands(parser):
  from .plugin import list as list_plugins
  subparsers = parser.add_subparsers(dest='cmd')
  default_command = None
  for command in list_plugins('command'):
    _log.info('add command ' + command.id)
    if hasattr(command, 'isDefault') and command.isDefault:
      default_command = command.id
    cmdparser = subparsers.add_parser(command.id)
    instance = command.load().factory(cmdparser)
    cmdparser.set_defaults(launcher=instance, launcherid=command.id)
  return default_command


def _set_runtime_infos(args):
  import os
  runtime = cc.view('_runtime')
  runtime.set('command', args.launcherid)
  runtime.set('reloader', args.use_reloader)
  cc.set('absoluteDir', os.path.abspath(cc.get('dir')) + '/')


def run():
  import argparse

  parser = argparse.ArgumentParser(description='Phovea Server')
  parser.add_argument('--use_reloader', action='store_true', help='whether to automatically reload the server')
  parser.add_argument('--env', default=cc.get('env'), help='environment mode (dev or prod)')

  # parse before to enable correct plugin discovery
  args = parser.parse_known_args()[0]
  if args.env.startswith('dev'):
    enable_dev_mode()
  else:
    enable_prod_mode()

  default_command = _resolve_commands(parser)
  if default_command is not None:
    set_default_subparser(parser, default_command)

  args = parser.parse_args()

  _set_runtime_infos(args)
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
