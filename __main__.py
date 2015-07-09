import os
import os.path
import sys
import argparse
import json

sys.path.append('plugins/')
print os.getcwd()
import caleydo.config as config

parser = argparse.ArgumentParser(description='Caleydo Web Server')
parser.add_argument('--dependencyOnly', action='store_true', help='just create the dependencies descriptions (bower, pip)')
parser.add_argument('--multithreaded' ,action='store_true', help='multi threaded using gevent')
parser.add_argument('--port', '-p', type=int, default=config.getint('port','caleydo.web'), help='server port')
parser.add_argument('--address', '-a', default=config.get('address','caleydo.web'), help='server address')
parser.add_argument('--use_reloader', action='store_true', help='whether to automatically reload the server')
args = parser.parse_args()


#append the plugin directories as primary lookup path
sys.path.extend(config.getlist('pluginDirs','caleydo'))

def run_server():
  """
  runs the webserver
  """
  #set configured registry
  import caleydo.plugin

  import dispatcher
  import mainapp

  #helper to plugin in function scope
  def loader(plugin):
    print 'add application: ' + plugin.id + ' at namespace: ' + plugin.namespace
    return lambda: plugin.load().factory()

  #create a path dispatcher
  applications = { p.namespace : loader(p) for p in caleydo.plugin.list('namespace') }

  #create a dispatcher for all the applications
  application = dispatcher.PathDispatcher(mainapp.default_app(), applications)

  if args.multithreaded or config.getboolean('multithreaded','caleydo.web'):
    print 'run multi-threaded'
    from geventwebsocket.handler import WebSocketHandler
    from gevent.wsgi import WSGIServer

    http_server = WSGIServer((args.address, args.port), application, handler_class=WebSocketHandler)
    http_server.serve_forever()
  else:
    print 'run single-threaded'
    from werkzeug.serving import run_simple
    run_simple(args.address, args.port, application, use_reloader=args.use_reloader or config.getboolean('use_reloader','caleydo.web'))
  #app.debug = True
  #print >>sy.stderr, 'map', app.url_map
  #app.run(host='0.0.0.0')

def dump_config():
  """
  just dumps the config to create the bower and pip requirements
  """
  import caleydo.plugin_parser
  p = caleydo.plugin_parser.parse()
  p.dump_bower()
  p.dump_pip()

if __name__ == '__main__':
  if args.dependencyOnly:
    dump_config()
  else:
    run_server()
