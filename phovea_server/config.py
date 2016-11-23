from __future__ import absolute_import
###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object
import os
import jsoncfg
from ._utils import replace_nested_variables, extend
import logging


_log = logging.getLogger(__name__)
_c = {}


def get(item, section=None, default=None):
  key = item if section is None else section + '.' + item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    act = act.get(p, {})
  v = act.get(keys[len(keys) - 1], None)

  def resolve(x):
    if '.' in x:  # assume absolute
      return get(x)
    else:
      return act.get(x, None)

  v = replace_nested_variables(v, resolve)
  # print key, v

  return v if v is not None else default


def set(item, value, section=None):
  key = item if section is None else section + '.' + item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    act = act.get(p, {})
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
  c = jsoncfg.load(config_file)
  extend(_c, {plugin_id: c})


def _init_config():
  from . import phovea_config
  f = phovea_config()
  _merge_config(f, 'phovea_server')
  global_ = os.path.abspath('config.json')
  if os.path.exists(global_) and global_ != f:
    extend(_c, jsoncfg.load(global_))

# create an initial config guess
_init_config()


def merge_plugin_configs(plugins):
  # merge all the plugins
  global _c
  _c = {}

  for plugin in plugins:
    f = plugin.config_file()
    if f:
      _log.info('merging config of %s', plugin.id)
      _merge_config(f, plugin.id)

  # override with more important settings
  if os.path.exists('config.json'):
    extend(_c, jsoncfg.load('config.json'))
