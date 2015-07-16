__author__ = 'Samuel Gratzl'

import json
import flask
import caleydo_server.plugin

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
  return json.dumps(obj, cls=JSONExtensibleEncoder, *args, **kwargs)

def jsonify(obj, *args, **kwargs):
  """
  similar to flask.jsonify but uses the extended json encoder and an arbitrary object
  :param obj:
  :param args:
  :param kwargs:
  :return:
  """
  return flask.Response(to_json(obj, *args, **kwargs), mimetype='application/json')

def glob_recursivly(path, match):
  import os
  import fnmatch

  for dirpath, dirnames, files in os.walk(path):
    for f in fnmatch.filter(files, match):
      yield os.path.join(dirpath, f)