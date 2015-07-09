from flask import Flask,Response,redirect,send_from_directory,safe_join,request
import os
import os.path
import plugin
import config

app = Flask(__name__)

@app.after_request
def add_header(response):
#  response.headers['Last-Modified'] = datetime.now()
  response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
  response.headers['Pragma'] = 'no-cache'
  response.headers['Expires'] = '-1'
  return response

@app.route('/')
def index():
  apps = [o.id for o in plugin.plugins() if os.path.exists(os.path.join(o.folder, 'index.html'))]
  if len(apps) == 1:
    return redirect('/' + apps[0] + '/')
  #generate a list of all known one
  text = ['<!DOCTYPE html><html><head lang="en"><meta charset="UTF-8"><title>Caleydo Web Apps</title></head><body><h1>Caleydo Web Apps</h1><ul>']
  text.extend(['<li><a href="/' + a + '/">' + a + '</a></li>' for a in apps])
  text.append('</li></body></html>')
  return '\n'.join(text)

#deliver config
@app.route('/config-gen.js')
def genconfig():
  #for which app main file
  application = request.args.get('app', None)
  reg = plugin.metadata().to_requirejs_config_file(application)

  #to specify the mime type even if it is a text
  return Response(response=reg, status=200, mimetype='application/javascript')

@app.route('/caleydo_web.js')
def gencore():
  #for which app main file
  application = request.args.get('app', None)
  #<script data-main="/config-gen.js" src="/bower_components/requirejs/require.js"></script>
  base = "(function() {{ \
    var headID = document.getElementsByTagName('head')[0]; \
    var newScript = document.createElement('script'); \
    newScript.type = 'text/javascript'; \
    newScript.src = '/bower_components/requirejs/require.js'; \
    newScript.setAttribute('data-main','/config-gen.js{0}'); \
    headID.appendChild(newScript); \
  }}())"
  code = base.format('' if application is None else '?app='+application)
  return Response(response=code, mimetype='application/javascript')

#deliver bower
@app.route('/bower_components/<path:path>')
def bowercomponents(path):
  return send_from_directory(config.get('clientDir','caleydo') + 'bower_components/', path)

#alternative name redirects
@app.route('/<string:app>/plugins/<path:path>')
def deliver_plugins(app, path):
  return redirect('/' + path)

@app.route('/<path:path>')
def deliver(path):
  print path
  if path.endswith('/'):
    path += 'index.html'
  for d in config.getlist('pluginDirs','caleydo'):
    d = os.path.abspath(d)
    dpath = safe_join(d, path)
    if os.path.exists(dpath):
      # send_static_file will guess the correct MIME type
      print 'sending',dpath
      return send_from_directory(d, path)
  return 'This page does not exist', 404

def default_app():
  app.debug = True
  return app
