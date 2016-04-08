__author__ = 'Samuel Gratzl'

import json
import caleydo_server.plugin
import pandas.json as ujson

class JSONExtensibleEncoder(json.JSONEncoder):
  """
  json encoder with extension point extensions
  """
  def __init__(self, *args, **kwargs):
    super(JSONExtensibleEncoder, self).__init__(*args, **kwargs)

    self.encoders = [p.load().factory() for p in caleydo_server.plugin.list('json-encoder')]

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
  #try:
  #  doesnt work since we can't convert numpy arrays
  #  import ujson
  #  return ujson.dumps(obj, cls=JSONExtensibleEncoder, *args, **kwargs)
  #except ImportError:
  if 'allow_nan' in kwargs:
    del kwargs['allow_nan']
  kwargs['ensure_ascii'] = False
  return ujson.dumps(obj, *args, **kwargs)

def jsonify(obj, *args, **kwargs):
  """
  similar to flask.jsonify but uses the extended json encoder and an arbitrary object
  :param obj:
  :param args:
  :param kwargs:
  :return:
  """
  import flask
  return flask.Response(to_json(obj, *args, **kwargs), mimetype='application/json')

def glob_recursivly(path, match):
  import os
  import fnmatch

  for dirpath, dirnames, files in os.walk(path):
    for f in fnmatch.filter(files, match):
      yield os.path.join(dirpath, f)

def fix_id(id):
  """
  fixes the id such that is it a resource identifier
  :param id:
  :return:
  """
  import re
  #convert strange characters to space
  r = re.sub(r"""[!#$%&'\(\)\*\+,\./:;<=>\?@\[\\\]\^`\{\|}~_]+""", ' ', id)
  #title case all words
  r = r.title()
  r = r[0].lower() + r[1:]
  #remove white spaces
  r = re.sub(r'\s+', '', r, flags=re.UNICODE)
  return r

def random_id(length):
  import string, random
  s=string.lowercase+string.digits
  id = ''
  for i in range(0,length):
    id += random.choice(s)
  return id
