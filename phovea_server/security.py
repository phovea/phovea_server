###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import str
from builtins import object
from typing import Dict, List, Union
from flask import Flask
from . import plugin as p


class User(object):
  def __init__(self, id: str, name: str = None, roles: List[str] = []):
    self.id: str = id
    self.name: str = name or id
    self.roles: List[str] = roles

  def has_role(self, role: str) -> bool:
    return role in self.roles


class SecurityManager(object):
  """
  a basic security manager
  """

  def __init__(self):
    pass

  def login_required(self, f):
    return f

  def login(self, username: str, extra_fields: Dict = {}) -> Union[User, None]:
    """logs the given user in
    :returns the logged in user object or None if login failed
    """
    return None

  def logout(self):
    """
    logs the current logged in user out
    """
    pass

  def init_app(self, app: Flask):
    """
    initializes the security manager with the main app
    """
    pass

  @property
  def current_user(self) -> Union[User, None]:
    """
    :returns the current logged in user
    """
    return None


ANONYMOUS_USER = User('ANONYMOUS')


class DummyManager(SecurityManager):
  """
  a dummy implementation of the security manager where everyone is authenticated
  """

  def login(self, username: str, extra_fields={}) -> Union[User, None]:
    return ANONYMOUS_USER

  @property
  def current_user(self) -> Union[User, None]:
    return ANONYMOUS_USER


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


def is_logged_in() -> bool:
  return manager().current_user is not None


def current_username() -> Union[str, None]:
  u = manager().current_user
  return u.name if hasattr(u, 'name') else None


def current_user() -> User:
  return manager().current_user


def login_required(f):
  """
  Decorator for views that require login.
  """
  return manager().login_required(f)


def init_app(app: Flask):
  """
  initializes this app by for login mechanism
  :param app:
  :return:
  """
  manager().init_app(app)


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
    if user is None:
      return False

  if not isinstance(item, dict):
    # assume we have an object
    item = {
      'creator': getattr(item, 'creator', ANONYMOUS_USER.name),
      'buddies': getattr(item, 'buddies', []),
      'group': getattr(item, 'group', ANONYMOUS_USER.name),
      'permissions': getattr(item, 'permissions', DEFAULT_PERMISSION)
    }

  owner, group, others, buddies = _decode(item.get('permissions', DEFAULT_PERMISSION))

  # I'm the creator
  if _is_equal(user.name, item.get('creator', ANONYMOUS_USER.name)) and permission in owner:
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
