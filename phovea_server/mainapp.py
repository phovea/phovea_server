###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import next
from . import ns
import os
import re

import logging

_log = logging.getLogger(__name__)


black_list = re.compile(r'(.*\.(py|pyc|gitignore|gitattributes)|(\w+)/((config|package)\.json|_deploy/.*))')
public_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public'))


def _is_on_black_list(path):
  # print 'check',path,black_list.match(path) is not None
  return black_list.match(path) is not None


def _deliver_production(path):
  # print path
  if path.endswith('/'):
    path += 'index.html'
  if _is_on_black_list(path):
    return 'This page does not exist', 404
  # serve public
  return ns.send_from_directory(public_dir, path)


def _deliver(path):
  # print path
  if path.endswith('/'):
    path += 'index.html'
  if _is_on_black_list(path):
    return 'This page does not exist', 404

  # serve public
  if os.path.exists(ns.safe_join(public_dir, path)):
    return ns.send_from_directory(public_dir, path)

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


def _generate_index():
  text = ["""
    <!DOCTYPE html><html><head lang="en">
    <meta charset="UTF-8"> <title>Caleydo Web Apps</title>
    <link href="//fonts.googleapis.com/css?family=Roboto:700,400" rel="stylesheet" type="text/css">
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
    text.append('<a class="appinfo" href="/' + app.id + '/"><span class="title">' + app.title + '</span><span class="name">' + app.name + '</span><span class="description">' + app.description + '</span></a>')
    text.append('<div class="links">')
    if app.homepage and app.homepage != '':
      text.append('<a href="' + app.homepage + '" target="_blank" class="homepage"><span>Visit homepage</span></a>')

    if app.repository and app.repository != '':
      text.append('<a href="' + app.repository + '" target="_blank" class="github"><span>Open repository</span></a>')

    text.append('</div>')
    text.append('</li>')

  text.append("""</ul> </nav> </main> <footer>
      <img src="assets/caleydo_c.svg" alt="Caleydo" width="20" height="20">
      <a href="http://caleydo.org">caleydo.org</a> </footer></div>
      <script src="assets/list.min.js"></script><script src="assets/main.js"></script>
      </body></html>
    """)
  return '\n'.join(text)


def _build_info():
  from codecs import open
  from .plugin import metadata

  dependencies = []
  plugins = []
  build_info = dict(plugins=plugins, dependencies=dependencies)

  requirements = 'requirements.txt'
  if os.path.exists(requirements):
    with open(requirements, 'r', encoding='utf-8') as f:
      dependencies.extend([l.strip() for l in f.readlines()])

  for p in metadata().plugins:
    if p.id == 'phovea_server':
      build_info['name'] = p.name
      build_info['version'] = p.version
      build_info['resolved'] = p.resolved
    else:
      desc = dict(name=p.name, version=p.version, resolved=p.resolved)
      plugins.append(desc)

  return ns.jsonify(build_info)


# health check for docker-compose, kubernetes
def _health():
    return 'ok', 200


def default_app():
  # from .config import view, _initialize
  from phovea_server import config
  # check initialization
  if config._c is None:
    config._initialize()
  app = ns.Namespace(__name__)
  cc = config.view('phovea_server')
  if cc.env.startswith('dev'):
    app.add_url_rule('/', 'index', _generate_index)
    app.add_url_rule('/index.html', 'index', _generate_index)
    app.add_url_rule('/<path:path>', 'deliver', _deliver)
  else:
    app.add_url_rule('/<path:path>', 'deliver', _deliver_production)
  app.add_url_rule('/api/buildInfo.json', 'build_info', _build_info)
  app.add_url_rule('/health', 'health', _health)
  return app
