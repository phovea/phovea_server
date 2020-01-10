###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import str
from builtins import object
from . import plugin as p
import sys

ANONYMOUS = 'anonymous'


class User(object):
  def __init__(self, id):
    self.id = id
    self.name = ANONYMOUS
    self.roles = [ANONYMOUS]

  def get_id(self):
    return str(self.id)

  @property
  def is_authenticated(self):
    return False

  @property
  def is_active(self):
    return False

  @property
  def is_anonymous(self):
    return self.name == ANONYMOUS

  def has_role(self, role):
    return role in self.roles

  def __eq__(self, other):
    """
    Checks the equality of two `UserMixin` objects using `get_id`.
    """
    if isinstance(other, User):
      return self.get_id() == other.get_id()
    return NotImplemented

  def __ne__(self, other):
    """
    Checks the inequality of two `UserMixin` objects using `get_id`.
    """
    equal = self.__eq__(other)
    if equal is NotImplemented:
      return NotImplemented
    return not equal

  if sys.version_info[0] != 2:  # pragma: no cover
    # Python 3 implicitly set __hash__ to None if we override __eq__
    # We set it back to its default implementation
    __hash__ = object.__hash__


ANONYMOUS_USER = User(ANONYMOUS)


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


def is_logged_in():
  return manager().is_authenticated()


def current_username():
  u = manager().current_user
  return u.name if hasattr(u, 'name') else ANONYMOUS


def current_user():
  user = manager().current_user
  if user.is_anonymous:
    return ANONYMOUS_USER
  return user


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


PERMISSION_READ = 4
PERMISSION_WRITE = 2
PERMISSION_EXECUTE = 1


def to_number(p_set):
  return (PERMISSION_READ if PERMISSION_READ in p_set else 0) + \
         (PERMISSION_WRITE if PERMISSION_WRITE in p_set else 0) + \
         (PERMISSION_EXECUTE if PERMISSION_EXECUTE in p_set else 0)


def to_string(p_set):
  return ('r' if PERMISSION_READ in p_set else '-') + \
         ('w' if PERMISSION_WRITE in p_set else '-') + \
         ('x' if PERMISSION_EXECUTE in p_set else '-')


def _from_number(p):
  r = set()
  if p >= 4:
    r.add(PERMISSION_READ)
    p -= 4
  if p >= 2:
    r.add(PERMISSION_WRITE)
    p -= 2
  if p >= 1:
    r.add(PERMISSION_EXECUTE)
  return r


DEFAULT_PERMISSION = 744


def _decode(permission=DEFAULT_PERMISSION):
  permission = int(permission)
  others = _from_number(permission % 10)
  group = _from_number((permission // 10) % 10)
  user = _from_number((permission // 100) % 10)
  buddies = _from_number((permission // 1000) % 10)
  return user, group, others, buddies


def _is_equal(a, b):
  if a == b:
    return True
  if not a or not b:
    return False
  a = a.lower()
  b = b.lower()
  return a == b


def _includes(items, item):
  if not item:
    return False
  for check in items:
    if _is_equal(check, item):
      return True
  return False


def can(item, permission, user=None):
  if user is None:
    user = current_user()

  if not isinstance(item, dict):
    # assume we have an object
    item = {
      'creator': getattr(item, 'creator', ANONYMOUS),
      'buddies': getattr(item, 'buddies', []),
      'group': getattr(item, 'group', ANONYMOUS),
      'permissions': getattr(item, 'permissions', DEFAULT_PERMISSION)
    }

  owner, group, others, buddies = _decode(item.get('permissions', DEFAULT_PERMISSION))

  # I'm the creator
  if _is_equal(user.name, item.get('creator', ANONYMOUS)) and permission in owner:
    return True

  # check if I'm in the buddies list
  if 'buddies' in item and _includes(item.get('buddies'), user.name) and permission in buddies:
    return True

  # check if I'm in the group
  if 'group' in item and _includes(user.roles, item.get('group')) and permission in group:
    return True

  return permission in others


def can_read(data_description, user=None):
  return can(data_description, PERMISSION_READ, user)


def can_write(data_description, user=None):
  return can(data_description, PERMISSION_WRITE, user)


def can_execute(data_description, user=None):
  return can(data_description, PERMISSION_EXECUTE, user)
