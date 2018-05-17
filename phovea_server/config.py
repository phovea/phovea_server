###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from __future__ import absolute_import
from builtins import object
import os
import jsoncfg
import codecs
from ._utils import replace_nested_variables, extend
import logging


_log = logging.getLogger(__name__)
_c = {}
_preMergeChanges = {}


def get(item, section=None, default=None):
  key = item if section is None else section + '.' + item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    act = act.get(p, {})
  last_key = keys[len(keys) - 1]

  if last_key not in act:
    # prop does not exist
    return default

  v = act[last_key]

  def resolve(x):
    if '.' in x:  # assume absolute
      return get(x)
    else:
      return act.get(x, None)

  v = replace_nested_variables(v, resolve)
  # print key, v

  return v


def set(item, value, section=None):
  global _c, _preMergeChanges
  key = item if section is None else section + '.' + item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    if p not in act:
      act[p] = {}
    act = act[p]
  act[keys[len(keys) - 1]] = value

  if _preMergeChanges is not None:
    # keep track of changes that were done before the recreation of the configuration
    act = _preMergeChanges
    for p in keys[0:-1]:
      if p not in act:
        act[p] = {}
      act = act[p]
    act[keys[len(keys) - 1]] = value


def getint(item, section=None, default=0):
  return int(get(item, section, default))


def getfloat(item, section=None, default=0.):
  return float(get(item, section, default))


def getboolean(item, section=None, default=False):
  return bool(get(item, section, default))


def getlist(item, section=None, separator='\n', default=[]):
  v = get(item, section, default)
  return v if isinstance(v, list) else v.split(separator)


def view(section):
  return CaleydoConfigSection(section)


class CaleydoConfigSection(object):
  def __init__(self, section):
    self._section = section

  def __getattr__(self, item):
    return self.get(item)

  def __getitem__(self, item):
    return self.get(item)

  def _expand(self, section=None):
    if self._section is None:
      return section
    return self._section + ('.' + section if section is not None else '')

  def get(self, item, section=None, default=None):
    return get(item, self._expand(section), default=default)

  def set(self, item, value, section=None):
    return set(item, value, self._expand(section))

  def getint(self, item, section=None, default=0):
    return getint(item, self._expand(section), default=default)

  def getfloat(self, item, section=None, default=0.):
    return getfloat(item, self._expand(section), default=default)

  def getboolean(self, item, section=None, default=False):
    return getboolean(item, self._expand(section), default=default)

  def getlist(self, item, section=None, separator='\n', default=[]):
    return getlist(item, self._expand(section), separator, default=default)

  def view(self, section):
    return CaleydoConfigSection(self._expand(section))


def _merge_config(config_file, plugin_id):
  _log.info(plugin_id)
  with codecs.open(config_file, 'r', 'utf-8') as fi:
    c = jsoncfg.loads(fi.read())
  extend(_c, {plugin_id: c})


def _init_config():
  from . import phovea_config
  f = phovea_config()
  _merge_config(f, 'phovea_server')
  global_ = os.path.abspath(os.environ.get('PHOVEA_CONFIG_PATH', 'config.json'))
  if os.path.exists(global_) and global_ != f:
    print('configuration file: ' + global_)
    with codecs.open(global_, 'r', 'utf-8') as fi:
      extend(_c, jsoncfg.loads(fi.read()))

# create an initial config guess
_init_config()


def merge_plugin_configs(plugins):
  # merge all the plugins
  global _c, _preMergeChanges
  _c = {}

  for plugin in plugins:
    f = plugin.config_file()
    if f:
      _log.info('merging config of %s', plugin.id)
      _merge_config(f, plugin.id)

  # override with more important settings
  global_ = os.path.abspath(os.environ.get('PHOVEA_CONFIG_PATH', 'config.json'))
  if os.path.exists(global_):
    with codecs.open(global_, 'r', 'utf-8') as fi:
      extend(_c, jsoncfg.loads(fi.read()))

  # merge changes done before the merge
  extend(_c, _preMergeChanges)
  _preMergeChanges = None
