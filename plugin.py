#will be injected
_registry = None

def _get_registry():
  global _registry
  if _registry is None:
    import _plugin_parser as pp
    metadata = pp.parse()
    import caleydo_server.config
    caleydo_server.config.merge_plugin_configs(metadata.plugins)
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

    if hasattr(m,'__call__'):
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
    #copy all values
    for key, value in desc.iteritems():
      self.__dict__[key] = value

class ExtensionDesc(AExtensionDesc):
  """
   plugin description
  """
  def __init__(self, desc):
    super(ExtensionDesc, self).__init__(desc)
    self._impl = None

    if not hasattr(self, 'module'):
      self.module = self.folder + '/' + self.file

    #from js notation to python notation
    self.module = self.module.replace('/','.')

  def load(self):
    if self._impl is None:
      import importlib
      print 'importing', self.module
      m = importlib.import_module(self.module)
      if hasattr(m,'_plugin_initialize'): #init method
        #import inspect
        #inspect.getcallargs()
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
    self._extensions.append(PreLoadedExtensionDesc(dict(type='manager',id='registry'), self))

    def loader(e):
      return lambda: e.load().factory()
    self._singletons = { e.id : loader(e) for e in self._extensions if e.type == 'manager'}

  def __len__(self):
    return len(self._extensions)

  def __getitem__(self, item):
    return self._extensions[item]

  def __iter__(self):
    return iter(self._extensions)

  def list(self, plugin_type = None):
    if plugin_type is None:
      return self
    if not hasattr(plugin_type, '__call__'): #not a callable
      bak = str(plugin_type)
      plugin_type = lambda x: x.type == bak

    return filter(plugin_type, self)

  def lookup(self, singleton_id):
    if singleton_id in self._singletons:
      return self._singletons[singleton_id]()
    return None

def list(plugin_type = None):
  return _get_registry().list(plugin_type)

def lookup(singleton_id):
  return _get_registry().lookup(singleton_id)

def plugins():
  return _get_registry().plugins

def metadata():
  return _get_registry().metadata