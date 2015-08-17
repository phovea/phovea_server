__author__ = 'Samuel Gratzl'

import caleydo_server.plugin as p

class User(object):
  def __init__(self):
    self.name = 'anonymous'
    self.roles = ['anonymous']
    self.is_authenticated = False

class SecurityManager(object):
  def __init__(self):
    pass

  def login_required(self, f):
    return f

  def login(self):
    return User()

  def logout(self):
    pass

  def current_user(self):
    return User()

  def init_app(self, app):
    pass

class DummyManager(SecurityManager):
  pass

_manager = None
def manager():
  global _manager
  if _manager is None:
    _manager = p.lookup('security_manager')
    if _manager is None:
      _manager = DummyManager()
  return _manager

def login_required(f):
  """
  Decorator for views that require login.
  """
  return manager().login_required(f)

def init_app(app):
  manager().init_app(app)