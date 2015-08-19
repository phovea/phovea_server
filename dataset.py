import flask
import caleydo_server.plugin
import caleydo_server.range
import caleydo_server.util
import itertools

app = flask.Flask(__name__)
app_idtype = flask.Flask(__name__)

#create the api application

_providers_r = None
def _providers():
  global _providers_r
  if _providers_r is None:
    _providers_r = [p.load().factory() for p in caleydo_server.plugin.list('dataset-provider')]
  return _providers_r

def iter():
  """
  an iterator of all known datasets
  :return:
  """
  return itertools.chain(*_providers())

def list_datasets():
  """
  list all known datasets
  :return:
  """
  return list(iter())

def _list_format_json(data):
  return caleydo_server.util.jsonify(data)

def _list_format_treejson(data):
  r = dict()
  for d in data:
    levels = d['fqname'].split('/')
    act = r
    for level in levels[:-1]:
      if level not in act:
        act[level] = dict()
      act = act[level]
    act[d['name']] = d
  return caleydo_server.util.jsonify(r, indent=1)

def _list_format_csv(data):
  delimiter = flask.request.args.get('f_delimiter',';')
  def gen():
    yield delimiter.join(['ID','Name','FQName','Type','Size','Entry'])
    for d in data:
      yield '\n'
      yield delimiter.join([str(d['id']), d['name'], d['fqname'], d['type'], ','.join(str(d) for d in d['size']), caleydo_server.util.to_json(d)])
  return flask.Response(gen(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=dataset.csv'})

def _to_query(query):
  keys = ['name', 'id', 'fqname', 'type']
  act_query = { k : v for k,v in query.iteritems() if k in keys}
  if len(act_query) == 0: #no query
    return lambda x : True
  import re
  def filter_elem(elem):
    return all((re.match(v, getattr(elem, k,'')) for k,v in act_query.iteritems()))
  return filter_elem

@app.route('/', methods=['GET','POST'])
def _list_datasets():
  if flask.request.method == 'GET':
    query = _to_query(flask.request.values)
    data = [d.to_description() for d in iter() if query(d)]

    limit = flask.request.values.get('limit',-1)
    if 0 < limit < len(data):
      data = data[:limit]

    format = flask.request.args.get('format','json')
    formats = dict(json=_list_format_json,treejson=_list_format_treejson,csv=_list_format_csv)
    if format not in formats:
      flask.abort(flask.make_response('invalid format: "{0}" possible ones: {1}'.format(format,','.join(formats.keys())), 400))
    return formats[format](data)
  else:
    return _upload_dataset(flask.request)

def get(dataset_id):
  """
  :param dataset_id:
  :return: returns the selected dataset identified by id
  """
  for p in _providers():
    r = p[dataset_id]
    if r is not None:
      return r
  return None

@app.route('/<dataset_id>', methods=['PUT','GET', 'DELETE'])
def _get_dataset(dataset_id):
  if flask.request.method == 'PUT':
    return _update_dataset(dataset_id, flask.request)
  elif flask.request.method == 'DELETE':
    return _remove_dataset(dataset_id)
  d = get(dataset_id)
  r = flask.request.args.get('range', None)
  if r is not None:
    r = range.parse(r)
  return caleydo_server.util.jsonify(d.asjson(r))

@app.route('/<dataset_id>/desc')
def _get_dataset_desc(dataset_id):
  d = get(dataset_id)
  return caleydo_server.util.jsonify(d.to_description())

def _dataset_getter(dataset_id, dataset_type):
  if isinstance(dataset_id, int) and dataset_id < 0:
    return [d for d in list_datasets() if d.type == dataset_type]
  t = get(dataset_id)
  if t is None:
    flask.abort(404) #,extra='invalid dataset id "'+str(dataset_id)+'"')
  if t.type != dataset_type:
    flask.abort(400) #,extra='the given dataset "'+str(dataset_id)+'" is not a '+dataset_type)
  return t

def _to_upload_desc(data_dict):
  if 'desc' in data_dict:
    import json
    return json.loads(data_dict['desc'])
  return data_dict

def _upload_dataset(request, id=None):
  #first choose the provider to handle the upload
  for p in _providers():
    r = p.upload(_to_upload_desc(request.values), request.files, id)
    if r:
      return caleydo_server.util.jsonify(r.to_description(),indent=1)
  #invalid upload
  flask.abort(400)

def add(desc, files = [], id = None):
  """
  adds a new dataset to this storage
  :param desc: the dict description information
  :param files: a list of FileStorage
  :param id: optional the unique id to use
  :return: the newly created dataset or None if an error occurred
  """
  for p in _providers():
    r = p.upload(desc, files, id)
    if r:
      return r
  return None

def update(dataset, desc, files = []):
  """
  updates the given dataset
  :param dataset: a dataset or a dataset id
  :param desc: the dict description information
  :param files: a list of FileStorage
  :return:
  """
  old = get(dataset) if isinstance(dataset,basestring) else dataset
  if old is None:
    return add(desc, files)
  r = old.update(desc, files)
  return r

def _update_dataset(dataset_id, request):
  old = get(dataset_id)
  if old is None:
    return _upload_dataset(request, dataset_id)
  r = old.update(_to_upload_desc(request.values), request.files)
  if r:
    return caleydo_server.util.jsonify(old.to_description(),indent=1)
  flask.abort(400)

def _remove_dataset(dataset_id):
  old = get(dataset_id)
  if old is None:
    flask.abort(404) #not found
  for p in _providers():
    if p.remove(old):
      return 'Successfully deleted '+dataset_id
  flask.abort(400)

def remove(dataset):
  """
  removes the given dataset
  :param dataset: a dataset or a dataset id
  :return: boolean whether the operation was successful
  """
  old = get(dataset) if isinstance(dataset,basestring) else dataset
  if old is None:
    return False
  for p in _providers():
    if p.remove(old):
      return True
  return False

def create_dataset():
  return app

def list_idtypes():
  tmp = dict()
  for d in list_datasets():
    for idtype in d.to_idtype_descriptions():
      tmp[idtype['id']] = idtype
  return tmp.values()

@app_idtype.route('/')
def _list_idtypes():
  return caleydo_server.util.jsonify(list_idtypes())

#add all specific handler
for handler in caleydo_server.plugin.list('dataset-specific-handler'):
  p = handler.load()
  p(app, _dataset_getter)

def create_idtype():
  return app_idtype

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9000)
