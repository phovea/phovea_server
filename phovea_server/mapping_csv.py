###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object, enumerate
import json
import os
from .config import view
from codecs import open


def merge(idtype, species):
  if not species:
    return idtype
  return idtype + '_' + species


class FileMapper(object):
  def __init__(self, desc, plugin):
    folder = plugin.folder + '/data/' if not hasattr(plugin, 'inplace') else plugin.folder
    self._path = os.path.join(folder, desc['path'])
    self._map = None
    self._desc = desc
    self.from_idtype = merge(desc['from'], desc.get('fromSpecies'))
    self.to_idtype = merge(desc['to'], desc.get('toSpecies'))
    pass

  def _load(self):
    import csv
    with open(self._path, 'r', 'utf-8') as csvfile:
      reader = csv.reader(csvfile, delimiter=self._desc.get('separator', ',').encode('ascii', 'ignore'), quotechar='"')
      self._map = dict()
      for i, line in enumerate(reader):
        if i == 0 and self._desc.get('header', False):
          continue
        key = line[0]
        values = line[1].split(self._desc.get('multi', ';'))
        self._map[key] = values

  def __call__(self, ids):
    if not self._map:
      self._load()
    return [self._map.get(id, None) for id in ids]


def to_files(plugins):
  for plugin in plugins:
    index = os.path.join(plugin.folder + '/data/' if not hasattr(plugin, 'inplace') else plugin.folder, 'mapping.json')
    if not os.path.isfile(index):
      continue
    with open(index, 'r') as f:
      desc = json.load(f)
      for di in desc:
        yield FileMapper(di, plugin)


class DataPlugin(object):
  def __init__(self, folder):
    # add a magic plugin for the static data dir
    self.inplace = True  # avoid adding the data suffix
    self.folder = folder
    self.id = os.path.basename(folder)


cc = view('phovea_server')
dataPlugin = DataPlugin(os.path.join(cc.dataDir, 'data'))


class StaticFileProvider(object):
  def __init__(self, plugins):
    self.files = list(to_files(plugins))

    self.files.extend(to_files([dataPlugin]))
    import glob
    extras = [DataPlugin(f) for f in (os.path.dirname(f) for f in glob.glob(cc.dataDir + '/*/mapping.json')) if
              os.path.basename(f) != 'data']
    self.files.extend(to_files(extras))

  def __iter__(self):
    return iter(((f.from_idtype, f.to_idtype, f) for f in self.files))


def create():
  """
  entry point of this plugin
  """
  from .plugin import plugins
  return StaticFileProvider(plugins())
