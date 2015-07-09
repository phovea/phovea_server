import re
import json
import os
import os.path
from collections import OrderedDict

bower_file = 'bower.json'
pip_file = 'requirements.txt'
bower_components_url = '/bower_components'
bower_components = 'bower_components'
metadata_file = '/package.json'

def _replace_variables(s):
  variables = {
    'baseUrl': bower_components_url
  }
  def match(m):
    if m.group(1) in variables:
      return variables[m.group(1)]
    print 'cant resolve ' + m.group(1)
    return '$unresolved$'

  return re.sub(r'\$\{(.*)\}', match, s)

def _unpack_eval(s):
  return re.sub(r'eval!(.*)', '\1', s)

def _unpack_python_eval(s):
  m = re.search(r'eval!(.*)', s)
  if m is None:
    return s
  return eval(m.group(1))


def _resolve_client_config(config):
  config = _replace_variables(config)
  config = _unpack_eval(config)
  return config

def _resolve_server_config(d):
  import six
  if isinstance(d, six.string_types): #not a string
    return _unpack_python_eval(_replace_variables(d))
  elif type(d) == list:
    return [_resolve_server_config(i) for i in d]
  elif type(d) == dict or type(d) == OrderedDict:
    for k,v in d.items():
      d[k] = _resolve_server_config(v)
    return d
  return d

# extend a dictionary recursivly
def _extend(target, w):
  for k,v in w.iteritems():
    if type(v) is dict:
      if k not in target:
        target[k] = _extend({}, v)
      else:
        target[k] = _extend(target[k], v)
    else:
      target[k] = v
  return target

def _list_dirs(dd):
  if not os.path.isdir(dd):
      return []
  return [d for d in os.listdir(dd) if not os.path.isfile(os.path.join(dd,d))]

def _resolve_conflicts(dependencies):
  r = dict()
  for k,v in dependencies.iteritems():
    if type(v) is list:
      print 'resolving versions of ',k,v,'->', ' '.join(v)
      r[k] = ' '.join(v)
    else:
      r[k] = v #single hit
  return r

class Plugin(object):
  def __init__(self, plugindir, p, desc):
    self.id = p
    self.name = desc.get('name', p)
    self.version = desc.get('version', '0.0.1')
    self.folder = os.path.join(plugindir, p)

class PluginMetaData(object):
  def __init__(self, cc):
    ccc = cc.view('caleydo')
    ccw = ccc.view('web')
    self.baseDir = ccc.clientDir
    self.config_file = self.baseDir + 'plugins/config-gen.js'
    self.baseServerDir = ccc.serverDir
    self.bower_dependencies = OrderedDict({})
    self.pip_dependencies = OrderedDict({})
    self.ignored_bower_dependencies = ['requirejs', 'require-css']

    self.plugins = []
    self.caleydo_client_plugins = []
    self.caleydo_server_plugins = []
    self.requirejs_config = {
      'baseUrl': ccw.baseUrl,
      'paths': OrderedDict(),
      'map': OrderedDict(),
      'deps': [ccw.mainFile],
      'config': OrderedDict()
    }
    self.requirejs_config['config'][ccw.configPrefix + 'caleydo/main'] = {
      'apiUrl': ccw.apiPrefix,
      'apiJSONSuffix': ccw.apiSuffix
    }
    self.requirejs_config['config'][ccw.configPrefix + 'caleydo/plugin'] = {
      'baseUrl': ccw.baseUrl,
      'plugins': self.caleydo_client_plugins
    }

  def _add_client_extension(self, plugins):
    if type(plugins) is not list:
      plugins = [ plugins ]
    self.caleydo_client_plugins.extend(plugins)

  def _add_server_extension(self, plugins):
    if type(plugins) is not list:
      plugins = [ plugins ]
    self.caleydo_server_plugins.extend(plugins)

  def _add_bower(self, dependencies, d):
    for k,v in dependencies.iteritems():
      if k in self.bower_dependencies:
        old = self.bower_dependencies[k]
        if (type(old) is not list and old == v) or (type(old) is list and v in old):
          pass
        elif type(old) is list:
          old.append(v)
        else:
          self.bower_dependencies[k] = [old, v]
      else:
        self.bower_dependencies[k] = v
    _extend(self.bower_dependencies, dependencies)

  def _add_pip(self, dependencies, d):
    _extend(self.pip_dependencies, dependencies)

  def _add_requirejs_config(self, rconfig, d):
    _extend(self.requirejs_config, rconfig)

  def _config_requirejs_bower(self, rconfig, d):
    if 'ignore' in rconfig:
      self.ignored_bower_dependencies.extend(rconfig['ignore'])

  def add_plugin(self, plugindir, d):
    metadata_file_abs = plugindir + d + metadata_file
    if not os.path.exists(metadata_file_abs):
      return
    print 'add plugin ' + metadata_file_abs
    with open(metadata_file_abs, 'r') as f:
      metadata = json.load(f)
      self.plugins.append(Plugin(plugindir, d, metadata))
      if 'dependencies' in metadata:
        self._add_bower(metadata['dependencies'], d)
      if 'caleydo' in metadata:
        c = metadata['caleydo']
        if 'plugins' in c:
          self._add_client_extension(c['plugins'])
        if 'python-server-plugins' in c:
          self._add_server_extension(c['python-server-plugins'])
        if 'requirejs-config' in c:
          self._add_requirejs_config(c['requirejs-config'], d)
        if 'requirejs-bower' in c:
          self._config_requirejs_bower(c['requirejs-bower'], d)
        if 'python-pip' in c:
          self._add_pip(c['python-pip'], d)


  def dump_bower(self):
    b = self.baseDir + bower_file
    if os.path.isfile(b):
      with open(self.baseDir + bower_file, 'r') as f:
        bower = json.load(f)
    else:
      bower = OrderedDict({
       "name": "caleydo-web",
       "version": "0.0.0",
      })
    bower['dependencies'] = _resolve_conflicts(self.bower_dependencies)
    with open(self.baseDir + bower_file,'w') as f:
      f.write(json.dumps(bower, indent=2))

  def dump_pip(self):
    with open(self.baseServerDir + pip_file, 'w') as f:
      for key, value in self.pip_dependencies.iteritems():
          f.write(key)
          f.write(value)
          f.write('\n')

  def _add_bower_requirejs_config(self, d):
    metadata_file_abs = self.baseDir + bower_components + '/' + d + '/.bower.json'
    print 'add bower dependency ' + metadata_file_abs
    with open(metadata_file_abs, 'r') as f:
      metadata = json.load(f)
    if 'main' in metadata:
      script = metadata['main']
      if type(script) is list:
        script = script[0]
      if re.match(r'.*\.js$', script):
        value = bower_components_url + '/' + d + '/' + script[:len(script) - 3]
        self.requirejs_config['paths'][d] = value
      elif re.match(r'.*\.css$', script):
        value = self.requirejs_config['map']['*']['css'] + '!' + bower_components_url + '/' + d + '/' + script[:len(script) - 4]
        self.requirejs_config['map']['*'][d] = value

  def derive_bower_requirejs_config(self):
    print 'derive bower config'
    for d in _list_dirs(self.baseDir + bower_components):
      if d in self.ignored_bower_dependencies:
        continue
      self._add_bower_requirejs_config(d)

  def to_requirejs_config_file(self, mainFile=None):
    bak = self.requirejs_config['deps']
    if mainFile is not None:
      self.requirejs_config['deps'] = [ mainFile ]
    c = json.dumps(self.requirejs_config, indent=2)
    c = _resolve_client_config(c)
    full = '/*global require */\r\nrequire.config(' + c + ');'
    self.requirejs_config['deps'] = bak
    return full

  @property
  def server_extensions(self):
    return _resolve_server_config(self.caleydo_server_plugins)

  def dump_config(self):
    full = self.to_config_file()
    with open(self.config_file, 'w') as f:
      f.write(full)
    print self.config_file + ' saved'

  def parse_dirs(self, plugindirs):
    for d in plugindirs:
      for f in _list_dirs(d):
          self.add_plugin(d, f)

def parse():
  import config as cc
  p = PluginMetaData(cc)
  p.parse_dirs(cc.getlist('pluginDirs','caleydo'))
  p.derive_bower_requirejs_config()

  return p