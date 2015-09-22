import json
import os
import os.path
from _utils import *

import caleydo_server.config

cc = caleydo_server.config.view('caleydo_server')

def is_disabled_plugin(p):
  def check(disable):
    return isinstance(disable,basestring) and re.match(disable, p.id)
  return any(map(check, cc.disable['plugins']))

def is_disabled_extension(extension, extension_type, p):
  if is_disabled_plugin(p):
    return True
  def check_elem(k,v):
    vk = extension_type if k == 'type' else extension['k']
    return re.match(v, vk)
  def check(disable):
    if isinstance(disable, basestring):
      return re.match(disable, extension['id'])
    return all(check_elem(k,v) for k,v in disable.iteritems())
  return any(map(check, cc.disable['extensions']))

def _resolve_server_config(d, vars = {}):
  import six
  if isinstance(d, six.string_types): #not a string
    return unpack_python_eval(replace_variables(d, vars))
  elif isinstance(d,list):
    return [_resolve_server_config(i) for i in d]
  elif isinstance(d, dict):
    for k,v in d.items():
      d[k] = _resolve_server_config(v)
    return d
  return d

# extend a dictionary recursivly
def _extend(target, w):
  for k,v in w.iteritems():
    if isinstance(v, dict):
      if k not in target:
        target[k] = _extend({}, v)
      else:
        target[k] = _extend(target[k], v)
    else:
      target[k] = v
  return target

class Plugin(object):
  def __init__(self, desc):
    self.id = desc['id']
    self.name = desc['name']
    self.version = desc['version']
    self.folder = desc['folder']
    self.folder_name = os.path.basename(self.folder)

class PluginMetaData(object):
  def __init__(self):
    with file('./registry.json') as f:
      data = json.load(f)

    self.plugins = filter(lambda x: not is_disabled_plugin(x), map(Plugin, data['plugins']))
    by_folder= { p.folder : p for p in self.plugins }
    self.caleydo_server_plugins = filter(lambda x : not is_disabled_extension(x, 'python', by_folder[x.folder]), data['extensions']['python'])

  @property
  def server_extensions(self):
    return _resolve_server_config(self.caleydo_server_plugins)

def parse():
  p = PluginMetaData()
  return p