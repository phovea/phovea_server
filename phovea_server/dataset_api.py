###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import str
from . import ns, plugin
from .util import jsonify, to_json
import logging
from .dataset import list_idtypes, iter, get_mappingmanager, get, list_datasets, add, remove


app = ns.Namespace(__name__)
app_idtype = ns.Namespace(__name__)

_log = logging.getLogger(__name__)


@app.errorhandler(ValueError)
def on_value_error(error):
  _log.error('ValueError: (' + str(error) + ') at ' + str(ns.request.environ))
  _log.error(error)
  return '<strong>{2} - {0}</strong><pre>{1}</pre>'.format('ValueError', error, 500), 500


def _list_format_json(data):
  return jsonify(data)


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
  return jsonify(r, indent=1)


def _list_format_csv(data):
  delimiter = ns.request.args.get('f_delimiter', ';')

  def to_size(size):
    if size is None:
      return ''
    if isinstance(size, list):
      return ','.join(str(d) for d in size)
    return str(size)

  def gen():
    yield delimiter.join(['ID', 'Name', 'FQName', 'Type', 'Size', 'Entry'])
    for d in data:
      yield '\n'
      yield delimiter.join(
          [str(d['id']), d['name'], d['fqname'], d['type'], to_size(d.get('size', None)), to_json(d)])

  return ns.Response(gen(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=dataset.csv'})


def _to_query(query):
  keys = ['name', 'id', 'fqname', 'type']
  act_query = {k: v for k, v in query.items() if k in keys}
  if len(act_query) == 0:  # no query
    return lambda x: True
  import re

  def filter_elem(elem):
    return all((re.match(v, getattr(elem, k, '')) for k, v in act_query.items()))

  return filter_elem


@app.route('/', methods=['GET', 'POST'])
@ns.etag
def _list_datasets():
  if ns.request.method == 'GET':
    query = _to_query(ns.request.values)
    data = [d.to_description() for d in iter() if query(d)]

    limit = ns.request.values.get('limit', -1)
    if 0 < limit < len(data):
      data = data[:limit]

    format = ns.request.args.get('format', 'json')
    formats = dict(json=_list_format_json, treejson=_list_format_treejson, csv=_list_format_csv)
    if format not in formats:
      ns.abort(
          ns.make_response('invalid format: "{0}" possible ones: {1}'.format(format, ','.join(list(formats.keys()))), 400))
    return formats[format](data)
  else:
    return _upload_dataset(ns.request)


@app.route('/<dataset_id>', methods=['PUT', 'GET', 'DELETE', 'POST'])
@ns.etag
def _get_dataset(dataset_id):
  if ns.request.method == 'PUT':
    return _update_dataset(dataset_id, ns.request)
  elif ns.request.method == 'POST':
    return _modify_dataset(dataset_id, ns.request)
  elif ns.request.method == 'DELETE':
    return _remove_dataset(dataset_id)
  d = get(dataset_id)
  if d is None:
    return 'invalid dataset id "' + str(dataset_id) + '"', 404
  if not d.can_read():
    return 'not allowed', 403
  return jsonify(d.asjson())


@app.route('/<dataset_id>/desc')
@ns.etag
def _get_dataset_desc(dataset_id):
  d = get(dataset_id)
  if not d:
    return 'invalid dataset id "' + str(dataset_id) + '"', 404
  if not d.can_read():
    return 'not allowed', 403
  return jsonify(d.to_description())


def _dataset_getter(dataset_id, dataset_type):
  if isinstance(dataset_id, int) and dataset_id < 0:
    return [d for d in list_datasets() if d.type == dataset_type]
  t = get(dataset_id)
  if t is None:
    ns.abort(404, 'invalid dataset id "' + str(dataset_id) + '"')
  if t.type != dataset_type:
    ns.abort(400, 'the given dataset "' + str(dataset_id) + '" is not a ' + dataset_type)
  if not t.can_read():
    ns.abort(403, 'not allowed')
  return t


def _to_upload_desc(data_dict):
  if 'desc' in data_dict:
    import json
    return json.loads(data_dict['desc'])
  return data_dict


def _upload_dataset(request, id=None):
  try:
    # first choose the provider to handle the upload
    r = add(_to_upload_desc(request.values), request.files, id)
    if r:
      return jsonify(r.to_description(), indent=1)
    # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def _update_dataset(dataset_id, request):
  try:
    old = get(dataset_id)
    if old is None:
      return _upload_dataset(request, dataset_id)
    if not old.can_write():
      return 'not allowed', 403
    r = old.update(_to_upload_desc(request.values), request.files)
    if r:
      return jsonify(old.to_description(), indent=1)
    # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def _modify_dataset(dataset_id, request):
  try:
    old = get(dataset_id)
    if old is None:
      return 'invalid dataset id "' + str(dataset_id) + '"', 404
    if not old.can_write():
      return 'not allowed', 403
    r = old.modify(_to_upload_desc(request.values), request.files)
    if r:
      return jsonify(old.to_description(), indent=1)
      # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def _remove_dataset(dataset_id):
  dataset = get(dataset_id)
  if dataset is None:
    return 'invalid dataset id "' + str(dataset_id) + '"', 404
  if not dataset.can_write():
    return 'not allowed', 403
  r = remove(dataset_id)
  if r:
    return jsonify(
        dict(state='success', msg='Successfully deleted dataset ' + dataset_id, id=dataset_id), indent=1)
  return 'invalid request', 400


def create_dataset():
  return app


@app_idtype.route('/')
@ns.etag
def _list_idtypes():
  return jsonify(list_idtypes())


@app_idtype.route('/<idtype>/')
@ns.etag
def _maps_to(idtype):
  mapper = get_mappingmanager()
  target_id_types = mapper.maps_to(idtype)
  return jsonify(target_id_types)


@app_idtype.route('/<idtype>/<to_idtype>', methods=['GET', 'POST'])
def _mapping_to(idtype, to_idtype):
  return _do_mapping(idtype, to_idtype)


@app_idtype.route('/<idtype>/<to_idtype>/search')
def _mapping_to_search(idtype, to_idtype):
  query = ns.request.args.get('q', None)
  max_results = int(ns.request.args.get('limit', 10))
  mapper = get_mappingmanager()
  if hasattr(mapper, 'search'):
    return jsonify(mapper.search(idtype, to_idtype, query, max_results))
  return jsonify([])


def _do_mapping(idtype, to_idtype):
  mapper = get_mappingmanager()
  args = ns.request.values
  first_only = args.get('mode', 'all') == 'first'

  if 'q' in args:
    names = args['q'].split(',')
  elif 'q[]' in args:
    names = args.getlist('q[]')
  else:
    ns.abort(400)
    return

  mapped_list = mapper(idtype, to_idtype, names)

  if first_only:
    mapped_list = [None if a is None or len(a) == 0 else a[0] for a in mapped_list]

  return jsonify(mapped_list)


# add all specific handler
for handler in plugin.list('dataset-specific-handler'):
  p = handler.load()
  p(app, _dataset_getter)


def create_idtype():
  return app_idtype


if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=9000)
