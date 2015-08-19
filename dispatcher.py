
class ApplicationProxy(object):
  """
  helper class for different applications defined by a namespace and a loader function
  """
  def __init__(self, namespace, loader):
    self.namespace = namespace
    #number of suburls to pop
    self.peeks = namespace.count('/')
    self.loader = loader
    self._impl = None

  @property
  def app(self):
    #cache
    if self._impl is not None:
      return self._impl
    self._impl = self.loader()
    return self._impl

  def match(self, path):
    return path.startswith(self.namespace)

class PathDispatcher(object):
  """
  helper class to select an application by path
  """
  def __init__(self, default_app, applications):
    self.default_app = default_app

    self.applications = [ ApplicationProxy(key,value) for key,value in applications.iteritems()]
    #print self.applications
    from threading import Lock
    self.lock = Lock()

  def get_application(self, path):
    with self.lock:
      for app in self.applications:
        if app.match(path):
          return app

  def __call__(self, environ, start_response):
    from werkzeug.wsgi import pop_path_info, get_path_info

    app = self.get_application(get_path_info(environ))
    if app is not None:
      for i in range(app.peeks):
        pop_path_info(environ)
      app = app.app
      #print get_path_info(environ), app
    else: #use default app
      app = self.default_app
    return app(environ, start_response)
