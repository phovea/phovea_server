import json
import csv
import os
import numpy as np
from caleydo_server.dataset_def import ADataSetEntry, ADataSetProvider


def assign_ids(ids, idtype):
  import caleydo_server.plugin

  manager = caleydo_server.plugin.lookup('idmanager')
  return np.array(manager(ids, idtype))

def fix_id(fqname):
  import caleydo_server.util
  return caleydo_server.util.fix_id(fqname)

class CSVEntry(ADataSetEntry):
  def __init__(self, desc, project):
    super(CSVEntry, self).__init__(desc['name'], project.id, desc['type'])
    self._desc = desc
    desc['fqname'] = self.fqname
    desc['id'] = self.id
    self._path = os.path.join(project.folder+'/data/',self._desc['path'])
    del self._desc['path']
    self._project = project

    self._loaded = None

  def load(self):
    if self._loaded is not None:
      return self._loaded

    data = []
    with open(self._path, 'r') as csvfile:
      reader = csv.reader(csvfile, delimiter=self._desc.get('separator', ',').encode('ascii','ignore'), quotechar='|')
      data.extend(reader)
    # print data
    def to_num(s):
      try:
        return float(s)  # for int, long and float
      except ValueError:
        return s

    data = [[to_num(i) for i in row] for row in data]

    # convert to col, row and data
    self._loaded = self._process(data)
    return self._loaded

  def _process(self, data):
    return data

  def to_description(self):
    return self._desc

  def idtypes(self):
    return [v for k, v in self._desc.iteritems() if k in ['rowtype', 'coltype', 'idtype']]


class CSVStratification(CSVEntry):
  def __init__(self, desc, project):
    super(CSVStratification, self).__init__(desc, project)
    self.idtype = desc['idtype']

  def _process(self, data):
    d = [dict(row=row[0], i=i, cluster=row[1]) for i, row in enumerate(data[1:])]

    def cmp(a, b):
      r = int(a['cluster'] - b['cluster'])
      return int(a['row'] - b['row']) if r == 0 else r

    d.sort(cmp)  # sort by cluster;
    clusters = dict()
    for di in d:
      c = di['cluster']
      if c in clusters:
        clusters[c].append(di['i'])
      else:
        clusters[c] = [di['i']]
    clusters = [dict(name=k, range=v) for k, v in clusters.iteritems()]

    rows = np.array([d[0] for d in data[1:]])
    return {
      "rows": rows,
      "rowIds": assign_ids(rows, self.idtype),
      "groups": clusters
    }

  def rows(self, range=None):
    n = self.load()['rows']
    if range is None:
      return n
    return n[range.asslice()]

  def rowids(self, range=None):
    n = self.load()['rowIds']
    if range is None:
      return n
    return n[range.asslice()]

  def asjson(self, range=None):
    return self.load()


class CSVMatrix(CSVEntry):
  def __init__(self, desc, project):
    super(CSVMatrix, self).__init__(desc, project)
    self.rowtype = desc['rowtype']
    self.coltype = desc['coltype']
    self.value = desc['value']['type']
    self.range = desc['value']['range']
    self.shape = desc['size']

  def _process(self, data):
    cols = np.array(data[0][1:])
    rows = np.array(map(lambda x: x[0], data[1:]))
    return {
      'cols': cols,
      'colIds': assign_ids(cols, self.coltype),
      'rows': rows,
      'rowIds': assign_ids(rows, self.rowtype),
      'data': np.array(map(lambda x: x[1:], data[1:]))
    }

  def rows(self, range=None):
    n = self.load()['rows']
    if range is None:
      return n
    return n[range.asslice()]

  def rowids(self, range=None):
    n = self.load()['rowIds']
    if range is None:
      return n
    return n[range.asslice()]

  def cols(self, range=None):
    n = self.load()['cols']
    if range is None:
      return n
    return n[range.asslice()]

  def colids(self, range=None):
    n = self.load()['colIds']
    if range is None:
      return n
    return n[range.asslice()]

  def asnumpy(self, range=None):
    n = self.load()['data']
    if range is None:
      return n
    return n[range[0].asslice(), range[1].asslice()]

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    cols = self.cols(None if range is None else range[1])
    rowids = self.rowids(None if range is None else range[0])
    colids = self.colids(None if range is None else range[1])

    r = dict(data=arr, rows=rows, cols=cols, rowIds=rowids, colIds=colids)
    return r


class CSVTable(CSVEntry):
  def __init__(self, desc, project):
    super(CSVTable, self).__init__(desc, project)
    print desc
    self.idtype = desc['idtype']
    self.columns = desc['columns']
    self.shape = desc['size']

  def _process(self, data):
    rows = np.array(map(lambda x: x[0], data[1:]))
    return {
      'rows': rows,
      'rowIds': assign_ids(rows, self.idtype),
      'data': map(lambda x: x[1:], data[1:])
    }

  def rows(self, range=None):
    n = self.load()['rows']
    if range is None:
      return n
    return n[range.asslice()]

  def rowids(self, range=None):
    n = self.load()['rowIds']
    if range is None:
      return n
    return n[range.asslice()]

  def asnumpy(self, range=None):
    n = self.load()['data']
    if range is None:
      return n
    return n[range[0].asslice()]

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    rowids = self.rowids(None if range is None else range[0])
    r = dict(data=arr, rows=rows, rowids=rowids)

    return r


class CSVVector(CSVEntry):
  def __init__(self, desc, project):
    super(CSVVector, self).__init__(desc, project)

    self.idtype = desc['idtype']
    self.value = desc['value']['type']
    self.range = desc['value']['range']
    self.shape = desc['size']

  def _process(self, data):
    rows = np.array(map(lambda x: x[0], data[1:]))
    return {
      'rows': rows,
      'rowIds': assign_ids(rows, self.idtype),
      'data': np.array(map(lambda x: x[1], data[1:]))
    }

  def rows(self, range=None):
    n = self.load()['rows']
    if range is None:
      return n
    return n[range.asslice()]

  def rowids(self, range=None):
    n = self.load()['rowIds']
    if range is None:
      return n
    return n[range.asslice()]

  def asnumpy(self, range=None):
    n = self.load()['data']
    if range is None:
      return n
    return n[range[0].asslice()]

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    rowids = self.rowids(None if range is None else range[0])
    r = dict(data=arr, rows=rows, rowIds=rowids)

    return r


def to_files(plugins):
  for plugin in plugins:
    index = os.path.join(plugin.folder+'/','data/index.json')
    if not os.path.isfile(index):
      continue
    with open(index, 'r') as f:
      desc = json.load(f)
      for di in desc:
        if di['type'] == 'matrix':
          yield CSVMatrix(di, plugin)
        elif di['type'] == 'table':
          yield CSVTable(di, plugin)
        elif di['type'] == 'vector':
          yield CSVVector(di, plugin)
        elif di['type'] == 'stratification':
          yield CSVStratification(di, plugin)


class StaticFileProvider(ADataSetProvider):
  def __init__(self, plugins):
    self.files = list(to_files(plugins))

  def __len__(self):
    return len(self.files)

  def __iter__(self):
    return iter(self.files)


def create():
  """
  entry point of this plugin
  """
  import caleydo_server.plugin
  return StaticFileProvider(caleydo_server.plugin.plugins())
