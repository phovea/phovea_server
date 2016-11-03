from phovea_server import ns
import os.path
import datetime
import phovea_server.util

last_deployment = ns.Namespace(__name__)

def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

"""
 Reads the modification date of the phovea_web_container/package.json
 OR as fallback (for builded bundles) the phovea_web_container/registry.json.
"""
@last_deployment.route('/', methods=['GET'])
def _last_deployment():
  path =  os.path.normpath(os.path.join(os.getcwd(), 'package.json'))

  if(os.path.exists(path) == False):
    path =  os.path.normpath(os.path.join(os.getcwd(), 'registry.json'))

  date = modification_date(path)
  print 'modification date of ' + path + ' = ' + str(date)
  return phovea_server.util.jsonify(dict(timestamp = date))

def create_last_deployment():
  return last_deployment
