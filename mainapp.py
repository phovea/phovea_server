import flask
import os
import os.path
import caleydo_server.plugin
import caleydo_server.config

app = flask.Flask(__name__)

@app.route('/')
def index(standard_app = caleydo_server.config.get('default_app','default_app',None)):
  if standard_app is not None:
    return flask.redirect(standard_app+'/')

  apps = [o.id for o in caleydo_server.plugin.plugins() if os.path.exists(os.path.join(o.folder, 'index.html'))]
  if len(apps) == 1:
    return flask.redirect(apps[0] + '/')
  #generate a list of all known one
  text = ['<!DOCTYPE html><html><head lang="en"><meta charset="UTF-8"><title>Caleydo Web Apps</title></head><body><h1>Caleydo Web Apps</h1><ul>']
  text.extend(['<li><a href="' + a + '/">' + a + '</a></li>' for a in apps])
  text.append('</li></body></html>')
  return '\n'.join(text)

@app.route('/apps.html')
def apps():
  return index()

#deliver config
@app.route('/config-gen.js')
def genconfig():
  #for which app main file
  application = flask.request.args.get('app', None)
  context = flask.request.args.get('context',None)
  reg = generate_config(application, context)
  #to specify the mime type even if it is a text
  return flask.Response(response=reg, status=200, mimetype='application/javascript')

def generate_config(application = None, context = None):
  reg = caleydo_server.plugin.metadata().to_requirejs_config_file(application, context)
  return reg

def generate_wrapper(application=None, context = None):
  #<script data-main="/config-gen.js" src="/bower_components/requirejs/require.js"></script>
  base = "(function() {{ \
    var headID = document.getElementsByTagName('head')[0]; \
    var newScript = document.createElement('script'); \
    newScript.type = 'text/javascript'; \
    newScript.src = '{1}/bower_components/requirejs/require.js'; \
    newScript.setAttribute('data-main','{1}/config-gen.js{0}'); \
    headID.appendChild(newScript); \
  }}())"
  code = base.format('' if application is None else '?app='+application, '' if context is None else context)
  return code

@app.route('/caleydo_web.js')
def gencore():
  #for which app main file
  application = flask.request.args.get('app', None)
  context = flask.request.args.get('context',None)
  code = generate_wrapper(application, context)
  return flask.Response(response=code, mimetype='application/javascript')

#deliver bower
@app.route('/bower_components/<path:path>')
def bowercomponents(path):
  return flask.send_from_directory(os.path.abspath(caleydo_server.config.get('bower_components','caleydo_server')), path)

#alternative name redirects
@app.route('/<string:app>/plugins/<path:path>')
def deliver_plugins(app, path):
  return flask.redirect('/' + path)

import re
black_list = re.compile(r'(.*\.(py|pyc|gitignore|gitattributes)|(\w+)/((config|package)\.json|_deploy/.*))')

def is_on_black_list(path):
  #print 'check',path,black_list.match(path) is not None
  return black_list.match(path) is not None

@app.route('/<path:path>')
def deliver(path):
  print path
  if path.endswith('/'):
    path += 'index.html'
  if is_on_black_list(path):
    return 'This page does not exist', 404

  for d in caleydo_server.config.getlist('pluginDirs','caleydo_server'):
    d = os.path.abspath(d)
    dpath = flask.safe_join(d, path)
    if os.path.exists(dpath):
      # send_static_file will guess the correct MIME type
      print 'sending',dpath
      return flask.send_from_directory(d, path)
  return 'This page does not exist', 404

def dump_generated_files(target_dir, application, context):
  with open(os.path.join(target_dir,'config-gen.js'),'w') as f :
    f.write(generate_config(application, context))
  with open(os.path.join(target_dir,'caleydo_web.js'),'w') as f :
    f.write(generate_wrapper(application, context))
  index_content = index(application)
  with open(os.path.join(target_dir,'index.html'),'w') as f :
    f.write(index_content)
  with open(os.path.join(target_dir,'apps.html'),'w') as f :
    f.write(index_content)

def default_app():
  return app
