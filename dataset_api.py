import flask
import caleydo_server.plugin
import caleydo_server.range
import caleydo_server.util

from .dataset import *

app = flask.Flask(__name__)
app_idtype = flask.Flask(__name__)

@app.errorhandler(ValueError)
def on_value_error(error):
  print 'ValueError: ('+str(error.message)+') at '+str(flask.request.environ)
  import traceback
  print traceback.format_exc()
  return '<strong>{2} - {0}</strong><pre>{1}</pre>'.format('ValueError', error.message, 500), 500

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
  def to_size(size):
    if size is None:
      return ''
    if isinstance(size, list):
      return ','.join(str(d) for d in size)
    return str(size)
  def gen():
    yield delimiter.join(['ID','Name','FQName','Type','Size','Entry'])
    for d in data:
      yield '\n'
      yield delimiter.join([str(d['id']), d['name'], d['fqname'], d['type'], to_size(d.get('size',None)), caleydo_server.util.to_json(d)])
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

@app.route('/<dataset_id>', methods=['PUT','GET', 'DELETE', 'POST'])
def _get_dataset(dataset_id):
  if flask.request.method == 'PUT':
    return _update_dataset(dataset_id, flask.request)
  elif flask.request.method == 'POST':
    return _modify_dataset(dataset_id, flask.request)
  elif flask.request.method == 'DELETE':
    return _remove_dataset(dataset_id)
  d = get(dataset_id)
  if d is None:
    return 'invalid dataset id "'+str(dataset_id)+'"', 404
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
    return 'invalid dataset id "'+str(dataset_id)+'"', 404
  if t.type != dataset_type:
    return 'the given dataset "'+str(dataset_id)+'" is not a '+dataset_type, 400
  return t

def _to_upload_desc(data_dict):
  if 'desc' in data_dict:
    import json
    return json.loads(data_dict['desc'])
  return data_dict

def _upload_dataset(request, id=None):
  try:
    #first choose the provider to handle the upload
    r = add(_to_upload_desc(request.values), request.files, id)
    if r:
      return caleydo_server.util.jsonify(r.to_description(),indent=1)
    #invalid upload
    return 'invalid upload', 400
  except ValueError, e:
    return on_value_error(e)

def _update_dataset(dataset_id, request):
  try:
    old = get(dataset_id)
    if old is None:
      return _upload_dataset(request, dataset_id)
    r = old.update(_to_upload_desc(request.values), request.files)
    if r:
      return caleydo_server.util.jsonify(old.to_description(),indent=1)
    #invalid upload
    return 'invalid upload', 400
  except ValueError, e:
    return on_value_error(e)

def _modify_dataset(dataset_id, request):
  try:
    old = get(dataset_id)
    if old is None:
      return 'invalid dataset id "'+str(dataset_id)+'"', 404
    r = old.modify(_to_upload_desc(request.values), request.files)
    if r:
      return caleydo_server.util.jsonify(old.to_description(),indent=1)
      #invalid upload
    return 'invalid upload', 400
  except ValueError, e:
    return on_value_error(e)

def _remove_dataset(dataset_id):
  dataset = get(dataset_id)
  if dataset is None:
    return 'invalid dataset id "'+str(dataset_id)+'"', 404
  r = remove(dataset_id)
  if r:
    return caleydo_server.util.jsonify(dict(state='success',msg='Successfully deleted dataset '+dataset_id,id=dataset_id),indent=1)
  return 'invalid request', 400

def create_dataset():
  return app

@app_idtype.route('/')
def _list_idtypes():
  return caleydo_server.util.jsonify(list_idtypes())

@app_idtype.route('/<idtype>/map')
def _map_ids(idtype):
  name = flask.request.args.get('id',None)
  if name is not None:
    return get_idmanager()([name], idtype)[0]
  names = flask.request.args.getlist('ids[]')
  return caleydo_server.util.jsonify(get_idmanager(names, idtype))

@app_idtype.route('/<idtype>/unmap')
def _unmap_ids(idtype):
  name = flask.request.args.get('id',None)
  if name is not None:
    return get_idmanager().unmap([int(name)], idtype)[0]
  names = caleydo_server.range.parse(flask.request.args.get('ids',''))[0].tolist()
  return caleydo_server.util.jsonify(get_idmanager().unmap(names, idtype))

@app_idtype.route('/<idtype>/')
def _maps_to(idtype):
  mapper = get_mappingmanager()
  target_id_types = mapper.maps_to(idtype)
  return caleydo_server.util.jsonify(target_id_types)

@app_idtype.route('/<idtype>/<to_idtype>')
def _mapping_to(idtype, to_idtype):
  return _do_mapping(idtype, to_idtype, False)

def _do_mapping(idtype, to_idtype, to_ids):
  mapper = get_mappingmanager()
  args = flask.request.args
  first_only = args.get('mode','all') == 'first'
  single = False

  if 'id' in args:
    names = get_idmanager().unmap([int(args['id'])], idtype)
    single = True
  elif 'ids' in args:
    names = get_idmanager().unmap(caleydo_server.range.parse(args['ids'])[0].tolist(), idtype)
  elif 'q' in args:
    names = args['q'].split(',')
    single = len(names) == 1
  else:
    flask.abort(400)
    return

  mapped_list = mapper(idtype, to_idtype, names)
  if first_only:
    mapped_list = [ None if a is None or len(a) == 0 else a[0] for a in mapped_list]

  if to_ids:
    m = get_idmanager()
    if first_only:
      mapped_list = m(mapped_list, to_idtype)
    else:
      mapped_list = [m(entry, to_idtype) for entry in mapped_list]

  if single:
    return mapped_list[0] if first_only else caleydo_server.util.jsonify(mapped_list[0])

  return caleydo_server.util.jsonify(mapped_list)

@app_idtype.route('/<idtype>/<to_idtype>/map')
def _mapping_to_id(idtype, to_idtype):
  return _do_mapping(idtype, to_idtype, True)


#add all specific handler
for handler in caleydo_server.plugin.list('dataset-specific-handler'):
  p = handler.load()
  p(app, _dataset_getter)

def create_idtype():
  return app_idtype

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9000)
