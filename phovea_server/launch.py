###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from gevent import monkey
monkey.patch_all()


import logging.config  # noqa: E402
import logging  # noqa: E402
from . import config  # noqa: E402


# set configured registry
def _get_config():
  # check initialization
  if config._c is None:
    config._initialize()
  return config.view('phovea_server')


# added for testing
def _get_config_hdf():
  # check initialization
  if config._c is None:
    config._initialize()
  return config.view('phovea_data_hdf')

cc = _get_config()

cc_hdf = _get_config_hdf()

# configure logging
logging.config.dictConfig(cc.logging)
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
  see https://stackoverflow.com/a/26378414

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
      for sp_name in list(x._name_parser_map.keys()):
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
  """
  Resolve commands from the phovea registy, loads the phovea extension, adds the instance to the command parser.
  """
  from .plugin import list as list_plugins

  # create a subparser
  subparsers = parser.add_subparsers(dest='cmd')

  default_command = None

  for command in list_plugins('command'):
    _log.info('add command ' + command.id)
    if hasattr(command, 'isDefault') and command.isDefault:
      default_command = command.id

    # create a argument parser for the command
    cmdparser = subparsers.add_parser(command.id)
    _log.info('loading and initializing the command: ' + command.id)

    # use the phovea extension point loading mechanism.
    # pass the parser as argument to the factory method so that the extension point (i.e., command)
    # can add further arguments to the parser (e.g., the address or port of the server).
    # the factory must return a launcher function, which gets the previously defined parser arguments as parameter.
    instance = command.load().factory(cmdparser)

    # register the instance as argument `launcher` and the command as `launcherid` to the command parser
    _log.info('add command instance to parser')
    cmdparser.set_defaults(launcher=instance, launcherid=command.id)

  return default_command


def _set_runtime_infos(args):
  """
  Set run time information, such as the executed command (registered as phovea extension point).
  The information is, for instance, used in the plugin.py when initializing the phovea registry.
  Additionally the configuration value `absoluteDir` is set.
  """
  import os
  runtime = cc.view('_runtime')
  runtime.set('command', args.launcherid)
  runtime.set('reloader', args.use_reloader)
  cc.set('absoluteDir', os.path.abspath(cc.get('dir')) + '/')


def run():
  """
  Run an application. The execution of the application can be configured using a command and arguments.
  Example terminal command:
  ```
  cd <workspace>
  python phovea_server --use_reloader --env dev api
  ```
  Supported arguments:
  `--use_reloader`: whether to automatically reload the server
  `--env`: environment mode (dev or prod)
  The last argument (e.g., `api`) is the command that must be registered as extension in the __init__.py and points to an execution file.
  Example:
  ```py
  registry.append('command', 'api', 'phovea_server.server', {'isDefault': True})
  ```
  The example registers the api command that runs the `create()` factory method from the server.py.
  """
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

  # resolve the default command to decide which application to launch
  default_command = _resolve_commands(parser)
  if default_command is not None:
    # set a default subparse to extract the defined arguments from the instance to the main arguments (?)
    set_default_subparser(parser, default_command)

  args = parser.parse_args()

  _set_runtime_infos(args)

  main = args.launcher(args)  # execute the launcher function, which returns another function

  if args.use_reloader:
    _log.info('start application using reloader...')
    run_with_reloader(main, extra_files=_config_files())
  else:
    _log.info('start application...')
    main()


def create_embedded():
  """
  Imports the phovea_server and creates an application
  """
  from .server import create_application
  return create_application()


# copied code of method run_with_reloader from werkzeug._reloader, because it causes import problems otherwise
def run_with_reloader(main_func, extra_files=None, interval=1, reloader_type="auto"):
  """Run the given function in an independent python interpreter."""
  import signal
  import os
  import sys
  import threading
  from werkzeug._reloader import reloader_loops, ensure_echo_on

  reloader = reloader_loops[reloader_type](extra_files, interval)
  signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
  try:
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
      ensure_echo_on()
      t = threading.Thread(target=main_func, args=())
      t.setDaemon(True)
      t.start()
      reloader.run()
    else:
      sys.exit(reloader.restart_with_reloader())
  except KeyboardInterrupt:
    pass
