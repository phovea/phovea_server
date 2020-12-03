###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object
import logging
from functools import cmp_to_key

_registry = None


def _get_registry():
  global _registry
  if _registry is None:
    from ._plugin_parser import parse
    metadata = parse()
    from .config import merge_plugin_configs, _c, _initialize
    # check initialization
    if _c is None:
      _initialize()
    merge_plugin_configs(metadata.plugins)
    _registry = Registry(metadata.plugins, metadata.server_extensions, metadata)
  return _registry


class Extension(object):
  """
   the loaded plugin instance
  """

  def __init__(self, desc, impl):
    self.desc = desc
    self.impl = impl
    self._cache = None

  def __call__(self, *args, **kwargs):
    """
     access and call the factory method of this plugin
    """
    if getattr(self.desc, 'singleton', False) and self._cache is not None:
      return self._cache

    m = getattr(self.impl, self.desc.factory)

    if hasattr(m, '__call__'):
      v = m(*args, **kwargs)
    else:
      v = m
    self._cache = v
    return v

  def factory(self, *args, **kwargs):
    return self(*args, **kwargs)


class AExtensionDesc(object):
  def __init__(self, desc):
    self.type = desc.get('type', 'unknown')
    self.id = desc['id']
    self.name = self.id
    self.factory = 'create'
    self.file = 'main'
    self.version = '1.0'
    self.description = ''
    # copy all values
    for key, value in desc.items():
      self.__dict__[key] = value


class ExtensionDesc(AExtensionDesc):
  """
   plugin description
  """

  def __init__(self, desc):
    super(ExtensionDesc, self).__init__(desc)
    self._impl = None

    # from js notation to python notation
    self.module = self.module.replace('/', '.')

  def load(self):
    if self._impl is None:
      import importlib
      _log = logging.getLogger(__name__)
      _log.info('importing %s', self.module)

      m = importlib.import_module(self.module)
      if hasattr(m, '_plugin_initialize'):  # init method
        # import inspect
        # inspect.getcallargs()
        m._plugin_initialize()

      self._impl = Extension(self, m)
    return self._impl


class PreLoadedExtensionDesc(AExtensionDesc):
  def __init__(self, desc, impl):
    super(PreLoadedExtensionDesc, self).__init__(desc)
    self._wrapper = PreLoadedExtension(impl)

  def load(self):
    return self._wrapper


class PreLoadedExtension(object):
  def __init__(self, impl):
    self._impl = impl

  def __call__(self, *args, **kwargs):
    return self._impl

  def factory(self, *args, **kwargs):
    return self._impl


class Registry(object):
  def __init__(self, plugins, extensions, metadata):
    self.plugins = plugins
    self.metadata = metadata
    self._extensions = [ExtensionDesc(p) for p in extensions]
    self._extensions.append(PreLoadedExtensionDesc(dict(type='manager', id='registry'), self))

    self._singletons = None

  @property
  def singletons(self):
    import collections
    from . import config
    # check initialization
    _log = logging.getLogger(__name__)
    if self._singletons is not None:
      return self._singletons

    def loader(e):
      return lambda: e.load().factory()

    # select singleton impl with lowest priority default 100
    mm = collections.defaultdict(lambda: [])
    for e in self._extensions:
      if e.type == 'manager':
        mm[e.id].append(e)

    if config._c is None:
      config._initialize()
    cc = config.view('phovea_server._runtime')
    current_command = cc.get('command', default='unknown')
    _log.info('read currently executed command from config: %s', current_command)

    def compare(a, b):
      a_prio = getattr(a, 'priority', 100)
      a_command = getattr(a, 'command', None)
      b_prio = getattr(b, 'priority', 100)
      b_command = getattr(b, 'command', None)
      # if the command matches the current command this has priority
      if a_command != b_command:
        if a_command == current_command:
          return -1
        elif b_command == current_command:
          return 1
      return a_prio - b_prio

    def select(v):
      v = sorted(v, key=cmp_to_key(compare))
      _log.info('creating singleton %s %s', v[0].id, getattr(v[0], 'module', 'server'))
      return loader(v[0])

    self._singletons = {k: select(v) for k, v in mm.items()}

    return self._singletons

  def __len__(self):
    return len(self._extensions)

  def __getitem__(self, item):
    return self._extensions[item]

  def __iter__(self):
    return iter(self._extensions)

  def list(self, plugin_type=None):
    if plugin_type is None:
      return self
    if not hasattr(plugin_type, '__call__'):  # not a callable
      return [x for x in self if x.type == plugin_type]
    return [x for x in self if plugin_type(x)]

  def lookup(self, singleton_id):
    if singleton_id in self.singletons:
      return self.singletons[singleton_id]()
    return None


def list(plugin_type=None):
  return _get_registry().list(plugin_type)


def lookup(singleton_id):
  return _get_registry().lookup(singleton_id)


def plugins():
  return _get_registry().plugins


def metadata():
  return _get_registry().metadata
