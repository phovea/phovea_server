import flask
import os.path
import datetime
import caleydo_server.util

last_deployment = flask.Flask(__name__)

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

"""
 Reads the modification date of the caleydo_web_container/package.json
 OR as fallback (for builded bundles) the caleydo_web_container/registry.json.
"""
@last_deployment.route('/', methods=['GET'])
def _last_deployment():
  path =  os.path.normpath(os.path.join(os.getcwd(), 'package.json'))

  if(os.path.exists(path) == False):
    path =  os.path.normpath(os.path.join(os.getcwd(), 'registry.json'))

  date = modification_date(path)
  print 'modification date of ' + path + ' = ' + str(date)
  return caleydo_server.util.jsonify(dict(timestamp = date))

def create_last_deployment():
  return last_deployment
