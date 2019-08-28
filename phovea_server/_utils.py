###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import str
import logging

_log = logging.getLogger(__name__)


# extend a dictionary recursively
def extend(target, w):
  for k, v in w.items():
    if isinstance(v, dict):
      if k not in target:
        target[k] = extend({}, v)
      else:
        target[k] = extend(target[k], v)
    else:
      target[k] = v
  return target


def replace_variables_f(s, lookup):
  import re
  s = str(s)
  if re.match(r'^\$\{([^}]+)\}$', s):  # full string is a pattern
    s = s[2:len(s) - 1]
    v = lookup(s)
    if v is None:
      _log.error('cant resolve ' + s)
      return '$unresolved$'
    return v

  def match(m):
    v = lookup(m.group(1))
    if v is None:
      _log.error('cant resolve ' + m.group(1))
      return '$unresolved$'
    return str(v)

  return re.sub(r'\$\{([^}]+)\}', match, s)


def replace_variables(s, variables):
  return replace_variables_f(s, lambda x: variables.get(x, None))


def replace_nested_variables(obj, lookup):
  if isinstance(obj, list):
    return [replace_nested_variables(o, lookup) for o in obj]
  elif isinstance(obj, str):
    return replace_variables_f(obj, lookup)
  elif isinstance(obj, dict):
    return {k: replace_nested_variables(v, lookup) for k, v in obj.items()}
  return obj
