__author__ = 'Samuel Gratzl'

import caleydo_server.plugin as p

class User(object):
  def __init__(self):
    self.name = 'anonymous'
    self.roles = ['anonymous']

    def is_authenticated(self):
      return False

    def is_active(self):
      return False

    def is_anonymous(self):
      return self.name == 'anonymous'

    def has_role(self, role):
      return role in self.roles

class SecurityManager(object):
  def __init__(self):
    pass

  def login_required(self, f):
    return f

  def login(self):
    return User()

  def logout(self):
    pass

  @property
  def current_user(self):
    return User()

  def is_authenticated(self):
    return self.current_user.is_authenticated()

  def has_role(self, role):
    return self.current_user.has_role(role)

  def init_app(self, app):
    pass

  def add_login_routes(self, app):
    pass

class DummyManager(SecurityManager):

  def is_authenticated(self):
    return True

  def has_role(self, role):
    return True

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

def add_login_routes(app):
  manager().add_login_routes(app)