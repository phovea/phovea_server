__author__ = 'Samuel Gratzl'
import os
import jsoncfg
from _utils import *

_c = {}

def __getattr__(item):
  return get(item)

def get(item, section=None, default=None):
  key = item if section is None else section+'.'+item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    act = act.get(p, {})
  v = act.get(keys[keys.length-1],None)

  def resolve(x):
    if '.' in x: #assume absolute
      return get(x)
    else:
      return act.get(x, None)

  if v is not None and type(v) is str:
    v = replace_nested_variables(v, resolve)

  return v if v is not None else default

def set(item, value, section=None):
  key = item if section is None else section+'.'+item
  keys = key.split('.')
  act = _c
  for p in keys[0:-1]:
    act = act.get(p, {})
  act[keys[keys.length-1]] = value

def getint(item, section=None):
  return int(get(item, section))

def getfloat(item, section=None):
  return float(get(item, section))

def getboolean(item, section=None):
  return bool(get(item, section))

def getlist(item, section=None, separator='\n'):
  v = get(item, section)
  return v.split(separator) if v is not None else []

def view(section):
  return CaleydoConfigSection(section)

class CaleydoConfigSection(object):
  def __init__(self, section):
    self._section = section

  def __getattr__(self, item):
    return self.get(item)

  def _expand(self, section=None):
    if self._section is None:
      return section if section is not None else 'DEFAULT'
    return self._section+('.'+section if section is not None else '')

  def get(self, item, section=None):
    return get(item, self._expand(section))

  def getint(self, item, section=None):
    return getint(item, self._expand(section))

  def getfloat(self, item, section=None):
    return getfloat(item, self._expand(section))

  def getboolean(self, item, section=None):
    return getboolean(item, self._expand(section))

  def getlist(self, item, section=None, separator='\n'):
    return getlist(item, self._expand(section), separator)

  def view(self, section):
    return CaleydoConfigSection(self._expand(section))

_c = {}
def _merge_config(config_file, plugin_id):
  c = jsoncfg.load(config_file)
  extend(_c, { plugin_id : c })

_own_config = os.path.dirname(os.path.abspath(__file__)) + '/config.json'
if os.path.exists(_own_config):
  _merge_config(_own_config, 'caleydo_server')

_web_config = os.path.dirname(os.path.abspath(__file__)) + '/../caleydo_web/config.json'
if os.path.exists(_web_config):
  _merge_config(_web_config, 'caleydo_web')

if os.path.exists('config.json'):
  extend(_c, jsoncfg.load('config.json'))

def merge_plugin_configs(plugins):

  global _c
  _c = {}
  for plugin in plugins:
    config_file = os.path.join(plugin.folder, 'config.json')
    if os.path.exists(config_file):
      print 'merging: ',config_file, plugin.id
      _merge_config(config_file, plugin.id)
  #override with more important settings
  if os.path.exists('config.json'):
    extend(_c, jsoncfg.load('config.json'))
