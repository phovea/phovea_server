###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from . import ns
import os
import re

app = ns.Namespace(__name__)
black_list = re.compile(r'(.*\.(py|pyc|gitignore|gitattributes)|(\w+)/((config|package)\.json|_deploy/.*))')


def is_on_black_list(path):
  # print 'check',path,black_list.match(path) is not None
  return black_list.match(path) is not None


@app.route('/')
def index():
  return generate_index()


@app.route('/<path:path>')
def deliver(path):
  # print path
  if path.endswith('/'):
    path += 'index.html'
  if is_on_black_list(path):
    return 'This page does not exist', 404

  # serve public
  d = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public'))
  if os.path.exists(ns.safe_join(d, path)):
    return ns.send_from_directory(d, path)

  # check all plugins
  elems = path.split('/')
  if len(elems) > 0:
    plugin_id = elems[0]
    elems[0] = 'build'
    from .plugin import plugins
    plugin = next((p for p in plugins() if p.id == plugin_id), None)
    if plugin:
      dpath = ns.safe_join(plugin.folder, '/'.join(elems))
      if os.path.exists(dpath):
        # send_static_file will guess the correct MIME type
        # print 'sending',dpath
        return ns.send_from_directory(plugin.folder, '/'.join(elems))

  return 'This page does not exist', 404


@app.route('/index.html')
def generate_index():
  text = [
      """
      <!DOCTYPE html><html><head lang="en">
      <meta charset="UTF-8"> <title>Caleydo Web Apps</title>
      <link href="//fonts.googleapis.com/css?family=Yantramanav:400,300" rel="stylesheet" type="text/css">
      <link href="assets/main.css" rel="stylesheet" type="text/css"></head>
      <body><div class="container"> <header>
      <h1><img src="assets/caleydo_text_right.svg" alt="Caleydo" width="200" height="40"> Web Apps</h1> </header>
      <main> <nav id="apps"> <input type="search" id="search" class="search" placeholder="Search App" autocomplete="off"/>
      <div class="keyboard-navigation-hint"> <span>Jump to an app:</span> <span><b>&#8593;</b><b>&#8595;</b> to navigate</span> <span><b>&#8629;</b> to select</span> </div>
      <ul class="list">
      """]

  # filter list and get title for apps
  from .plugin import plugins
  apps = sorted((p for p in plugins() if p.is_app()), key=lambda p: p.title)

  for app in apps:
    text.append('<li>')
    text.append(
        '<a class="appinfo" href="/' + app.id + '/"><span class="title">' + app.title + '</span><span class="name">' + app.name + '</span><span class="description">' + app.description + '</span></a>')
    text.append('<div class="links">')
    if app.homepage and app.homepage != '':
      text.append('<a href="' + app.homepage + '" target="_blank" class="homepage"><span>Visit homepage</span></a>')

    if app.repository and app.repository != '':
      text.append('<a href="' + app.repository + '" target="_blank" class="github"><span>Open repository</span></a>')

    text.append('</div>')
    text.append('</li>')

  text.append(
      """</ul> </nav> </main> <footer>
        <img src="assets/caleydo_c.svg" alt="Caleydo" width="20" height="20">
        <a href="http://caleydo.org">caleydo.org</a> </footer></div>
        <script src="assets/list.min.js"></script><script src="assets/main.js"></script>
        </body></html>
      """)
  return '\n'.join(text)


def default_app():
  return app
