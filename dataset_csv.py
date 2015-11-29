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
    super(CSVEntry, self).__init__(desc['name'], project.id, desc['type'], desc.get('id',None))
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

    header = data[0]
    data = [[to_num(v) if i > 0 else v for i,v in enumerate(row)] for row in data[1:]]
    data.insert(0, header)

    # convert to col, row and data
    self._loaded = self._process(data)
    return self._loaded

  def _process(self, data):
    return data

  def to_description(self):
    return self._desc

  def idtypes(self):
    return [v for k, v in self._desc.iteritems() if k in ['rowtype', 'coltype', 'idtype']]

def guess_color(name, i):
  name = name.lower()
  colors = dict(name='blue',female='red',deceased='#e41a1b',living='#377eb8')
  if name in colors:
    return colors[name]
  l = ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd',
          '#ccebc5', '#ffed6f']
  return l[i%len(l)]

class CSVStratification(CSVEntry):
  def __init__(self, desc, project):
    super(CSVStratification, self).__init__(desc, project)
    self.idtype = desc['idtype']
    for i,g in enumerate(desc['groups']):
      if 'color' not in g:
        g['color'] = guess_color(g['name'], i)

  def _process(self, data):
    d = [dict(row=row[0], i=i, cluster=row[1]) for i, row in enumerate(data[1:])]

    def cmp(a, b):
      r = int(a['cluster'] - b['cluster'])
      if r != 0:
        return r
      ra = a['row']
      rb = b['row']
      if ra == rb:
        return 0
      return -1 if ra < rb else +1

    d.sort(cmp)  # sort by cluster;
    clusters = dict()
    for di in d:
      c = di['cluster']
      if c in clusters:
        clusters[c].append(di['i'])
      else:
        clusters[c] = [di['i']]

    colors= { g['name']: g['color'] for g in self._desc['groups'] }
    clusters = [dict(name=k, range=v, color=colors.get(k,'gray')) for k, v in clusters.iteritems()]

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

  @staticmethod
  def parse(data, path, project, id = None):
    desc = dict(type='stratification',
                name=data.get('name','Uploaded File'),
                path = os.path.basename(path),
                idtype=data.get('idtype',data.get('rowtype','unknown')))
    for k,v in data.iteritems():
      if k not in desc:
        desc[k] = v
    if id is not None:
      desc['id'] = id
    if 'size0' in data and 'ngroups' in data:
      desc['size'] = [int(data['size0'])]
      del desc['size0']
      desc['ngroups'] = int(data['ngroups'])
    else: #derive from the data
      clusters = set()
      count = 0
      with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=desc.get('separator', ',').encode('ascii','ignore'), quotechar='|')
        for row in reader:
          count+=1
          clusters.add(row[1])
      desc['size'] = [ count ]
      desc['ngroups'] = len(clusters)

    return CSVStratification(desc, project)


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
    is_number = self.value == 'real' or self.value == 'int'

    if is_number:
      vs = map(lambda x: [np.NaN if v == 'NA' or v == '' else v for v in x[1:]], data[1:])
      #import numpy.ma as ma
      #dd = ma.masked_equal(np.array(vs), np.NaN)
      dd = np.array(vs)
    else:
      dd = np.array(map(lambda x: x[1:], data[1:]))
    return {
      'cols': cols,
      'colIds': assign_ids(cols, self.coltype),
      'rows': rows,
      'rowIds': assign_ids(rows, self.rowtype),
      'data': dd
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

    rows = range[0].asslice()
    cols = range[1].asslice()
    d = None
    if isinstance(rows, list) and isinstance(cols, list):
      #fancy indexing in two dimension doesn't work
      d_help = n[rows,:]
      d = d_help[:,cols]
    else:
      d = n[rows, cols]
    return d

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    cols = self.cols(None if range is None else range[1])
    rowids = self.rowids(None if range is None else range[0])
    colids = self.colids(None if range is None else range[1])

    r = dict(data=arr, rows=rows, cols=cols, rowIds=rowids, colIds=colids)
    return r

  @staticmethod
  def parse(data, path, project, id = None):
    desc = dict(type='matrix',
                name=data.get('name','Uploaded File'),
                path = os.path.basename(path),
                rowtype=data.get('rowtype','unknown'),
                coltype=data.get('coltype','unknown'),
                value=dict(type=data.get('value_type','real')))
    for k,v in data.iteritems():
      if k not in desc:
        desc[k] = v
    if id is not None:
      desc['id'] = id

    if all((k in data) for k in ['size0','size1','value_min','value_max']):
      desc['size'] = [int(data['size0']),int(data['size1'])]
      del desc['size0']
      del desc['size1']
      desc['value']['range'] = [float(data['value_min']),float(data['value_max'])]
      del desc['value_min']
      del desc['value_max']
    else: #derive from the data
      rows = 0
      cols = None
      min_v = None
      max_v = None
      with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=desc.get('separator', ',').encode('ascii','ignore'), quotechar='|')
        for row in reader:
          if cols is None:
            cols = len(row)-1
          else:
            rows+=1
            min_act = min(map(float, row[1:]))
            min_v = min_act if min_v is None else min(min_act, min_v)
            max_act = max(map(float, row[1:]))
            max_v = max_act if max_v is None else max(max_act, max_v)
      desc['size'] = [rows, cols]
      desc['value']['range'] = [float(data['value_min']) if 'value_min' in data else min_v, float(data['value_max']) if 'value_max' in data else max_v]

    return CSVMatrix(desc, project)


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

  @staticmethod
  def parse(data, path, id = None):
    pass


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

  @staticmethod
  def parse(data, path, project, id = None):
    pass


def to_files(plugins):
  for plugin in plugins:
    index = os.path.join(plugin.folder,'data/index.json')
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


class DataPlugin(object):
  def __init__(self):
    #add a magic plugin for the static data dir
    from caleydo_server.config import view
    cc = view('caleydo_server')
    self.folder = cc.dataDir
    self.id = 'data'

  def save(self, f):
    import werkzeug.utils
    import caleydo_server.util
    dir_ = os.path.join(self.folder,'data')
    if not os.path.exists(dir_):
      os.makedirs(dir_)
    filename = os.path.basename(f.filename)
    filename = werkzeug.utils.secure_filename(filename+caleydo_server.util.random_id(3)+'.csv')
    path = os.path.join(dir_, filename)
    f.save(path)
    return path

  def append(self, desc, path):
    desc['path'] = os.path.basename(path)
    index = os.path.join(self.folder,'data/index.json')
    old = []
    if os.path.isfile(index):
      with open(index,'r') as f:
        old = json.load(f)
    old.append(desc)
    with open(index,'w') as f:
        json.dump(old, f, indent=1)


dataPlugin = DataPlugin()

class StaticFileProvider(ADataSetProvider):
  def __init__(self, plugins):

    self.files = list(to_files(plugins))

    self.files.extend(to_files([dataPlugin]))

  def __len__(self):
    return len(self.files)

  def __iter__(self):
    return iter(self.files)

  def upload(self, data, files, id=None):
    if 'csv' != data.get('_provider', 'csv'):
      return None #not the right provider
    type = data.get('type','unknown')
    parsers = dict(matrix=CSVMatrix.parse,table=CSVTable.parse,vector=CSVVector.parse,stratification=CSVStratification.parse)
    if type not in parsers:
      return None #unknown type
    f = files[files.keys()[0]]
    path = dataPlugin.save(f)
    r = parsers[type](data, path, dataPlugin, id)
    if r:
      dataPlugin.append(r._desc, path)
      self.files.append(r)
    else:
      os.remove(path) #delete file again
    return r

def create():
  """
  entry point of this plugin
  """
  import caleydo_server.plugin
  return StaticFileProvider(caleydo_server.plugin.plugins())
