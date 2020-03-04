###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import range
import json
from typing import Union


class JSONExtensibleEncoder(json.JSONEncoder):
  """
  json encoder with extension point extensions
  """

  def __init__(self, *args, **kwargs):
    super(JSONExtensibleEncoder, self).__init__(*args, **kwargs)

    from .plugin import list as list_plugins
    self.encoders = [p.load().factory() for p in list_plugins('json-encoder')]

  def default(self, o):
    for encoder in self.encoders:
      if o in encoder:
        return encoder(o, self)
    return super(JSONExtensibleEncoder, self).default(o)


def to_json(obj, *args, **kwargs):
  """
  convert the given object ot json using the extensible encoder
  :param obj:
  :param args:
  :param kwargs:
  :return:
  """
  if 'allow_nan' in kwargs:
    del kwargs['allow_nan']
  if 'indent' in kwargs:
    del kwargs['indent']
  kwargs['ensure_ascii'] = False

  # Pandas JSON module has been deprecated and removed. UJson cannot convert numpy arrays, so it cannot be used here. The JSON used here does not support the `double_precision` keyword.
  if isinstance(obj, float) or isinstance(obj, dict) or isinstance(obj, list):
    obj = _handle_nan_values(obj)
  return json.dumps(obj, cls=JSONExtensibleEncoder, *args, **kwargs)


def _handle_nan_values(obj_to_convert: Union[dict, list, float]) -> Union[dict, list, None]:
    """
    Convert any NaN values in the given object to None. Previously, Pandas was used to encode NaN to null. This feature has been deprecated and removed, therefore
    the standard JSON encoder is used which parses NaN instead of null. A custom JSON encoder does not work for converting these values to None because python's
    JSON encoder already knows how to serialize NaN values.
    :param obj_to_convert:
    :return dict, list or None:
    """
    import math
    converted_dict = {}
    converted_list = []
    # primitive value
    if (isinstance(obj_to_convert, float) and math.isnan(obj_to_convert)):
      return None
    # convert dictionaries
    if isinstance(obj_to_convert, dict):
      for k, v in obj_to_convert.items():
          # value is dictionary or list
          if isinstance(v, dict) or isinstance(v, list):
              converted_dict[k] = _handle_nan_values(v)
          else:
              # value is NaN
              if (isinstance(v, float) and math.isnan(v)):
                  converted_dict[k] = None
              else:
                  converted_dict[k] = v
      return converted_dict
    # convert lists
    elif isinstance(obj_to_convert, list):
      for elem in obj_to_convert:
        # list element is dictionary
        if isinstance(elem, dict):
          converted_list.append(_handle_nan_values(elem))
        # list element is NaN value
        elif (isinstance(elem, float) and math.isnan(elem)):
          converted_list.append(None)
        else:
          converted_list.append(elem)
      return converted_list


def jsonify(obj, *args, **kwargs):
  """
  similar to flask.jsonify but uses the extended json encoder and an arbitrary object
  :param obj:
  :param args:
  :param kwargs:
  :return:
  """
  from .ns import Response
  return Response(to_json(obj, *args, **kwargs), mimetype='application/json; charset=utf-8')


def glob_recursivly(path, match):
  import os
  import fnmatch

  for dirpath, dirnames, files in os.walk(path):
    if match is None:
      return None
    for f in fnmatch.filter(files, match):
      yield os.path.join(dirpath, f)


def fix_id(id):
  """
  fixes the id such that is it a resource identifier
  :param id:
  :return:
  """
  import re
  # convert strange characters to space
  r = re.sub(r"""[!#$%&'\(\)\*\+,\./:;<=>\?@\[\\\]\^`\{\|}~_]+""", ' ', id)
  # title case all words
  r = r.title()
  r = r[0].lower() + r[1:]
  # remove white spaces
  r = re.sub(r'\s+', '', r, flags=re.UNICODE)
  return r


def random_id(length):
  import string
  import random
  s = string.ascii_lowercase + string.digits
  id = ''
  for i in range(0, length):
    id += random.choice(s)
  return id
