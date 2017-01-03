###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import str
from builtins import object
from . import plugin as p
import sys


class User(object):
  def __init__(self, id):
    self.id = id
    self.name = 'anonymous'
    self.roles = ['anonymous']

  def get_id(self):
    try:
      return str(self.id)  # python 2
    except NameError:
      return str(self.id)  # python 3

  @property
  def is_authenticated(self):
    return False

  @property
  def is_active(self):
    return False

  @property
  def is_anonymous(self):
    return self.name == 'anonymous'

  def has_role(self, role):
    return role in self.roles

  def __eq__(self, other):
    '''
    Checks the equality of two `UserMixin` objects using `get_id`.
    '''
    if isinstance(other, User):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    '''
    Checks the inequality of two `UserMixin` objects using `get_id`.
    '''
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal

  if sys.version_info[0] != 2:  # pragma: no cover
    # Python 3 implicitly set __hash__ to None if we override __eq__
    # We set it back to its default implementation
    __hash__ = object.__hash__


class SecurityManager(object):
  """
  a basic security manager
  """

  def __init__(self):
    pass

  def login_required(self, f):
    return f

  def login(self, username, extra_fields={}):
    """logs the given user in
    :returns the logged in user object or None if login failed
    """
    return User('')

  def logout(self):
    """
    logs the current logged in user out
    """
    pass

  @property
  def current_user(self):
    """
    :returns the current logged in user
    """
    return User('')

  def is_authenticated(self):
    """whether the current user is authenticated
    """
    return self.current_user.is_authenticated

  def has_role(self, role):
    """whether the current use has the role
    """
    return self.current_user.has_role(role)

  def init_app(self, app):
    pass

  def add_login_routes(self, app):
    pass


class DummyManager(SecurityManager):
  """
  a dummy implementation of the security manager where everyone is authenticated
  """

  def is_authenticated(self):
    return True

  def has_role(self, role):
    return True


_manager = None


def manager():
  """
  :return: the security manager
  """
  global _manager
  if _manager is None:
    _manager = p.lookup('security_manager')
    if _manager is None:
      _manager = DummyManager()
  return _manager


def current_username():
  u = manager().current_user
  return u.name if hasattr(u, 'name') else 'Anonymous'


def login_required(f):
  """
  Decorator for views that require login.
  """
  return manager().login_required(f)


def init_app(app):
  """
  initializes this app by for login mechanism
  :param app:
  :return:
  """
  manager().init_app(app)


def add_login_routes(app):
  """
  initializes this flask for providing access to /login and /logout
  :param app:
  :return:
  """
  manager().add_login_routes(app)
