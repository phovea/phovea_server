__author__ = 'Samuel Gratzl'

import flask
import range as ranges
from util import jsonify
import caleydo_server.plugin



def asrange(r):
  if r is None:
    return None
  return ranges.parse(r)

def format_json(dataset, range, args):
  d = dataset.asjson(range)
  if bool(args.get('f_pretty_print', False)):
    return jsonify(d, indent=' ')
  return jsonify(d)

def format_csv(dataset, range, args):
  include_rows = bool(args.get('f_rows', False))
  include_cols = bool(args.get('f_cols', False))
  delimiter = args.get('f_delimiter',';')

  import StringIO, itertools

  def gen():
    f = StringIO.StringIO()
    if include_cols and dataset.type == 'matrix':
      cols = dataset.cols(range[1] if range is not None else None)
      header = delimiter.join(cols)
    elif dataset.type == 'table':
      header = delimiter.join([d.name for d in dataset.columns])
    else:
      header = ''
    d = dataset.asnumpy(range)
    import numpy
    numpy.savetxt(f, d, header=header, delimiter=delimiter)
    if not include_rows:
      yield f.getvalue()
      return

    #extend with the row ids
    rows = dataset.rows(range[0] if range is not None else None)
    yield dataset.idtype if dataset.type == 'table' else dataset.rowtype
    yield delimiter
    yield f.readline()
    yield '\n'
    for row, line in itertools.izip(rows, f):
      yield row
      yield delimiter
      yield line
      yield '\n'

  return flask.Response(gen(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename='+dataset.name+'.csv'})

def format_image(dataset, range, args):
  format = args.get('format','png')

  import scipy.misc
  import io

  #TODO set a palette to specify colors instead of gray scales
  #how to interpolate / sample colors - which space?
  minmax = dataset.range
  img = scipy.misc.toimage(dataset.asnumpy(range), cmin=minmax[0], cmax=minmax[1])
  b = io.BytesIO()
  img.save(b, format=format)
  b.seek(0)
  return flask.send_file(b, mimetype='image/'+format.replace('jpg','jpeg'))

def resolve_formatter(type, format):
  for p in caleydo_server.plugin.list(type+'-formatter'):
    if p.format == format:
      return p.load()
  flask.abort(400,'unknown format "{0}" possible formats are: {1}'.format(format, ','.join((p.format for p in plugin.list(type+'-formatter')))))

def _add_handler(app, dataset_getter, type):
  def desc_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    return jsonify(d.to_description())

  app.add_url_rule('/'+type+'/<int:dataset_id>','desc_'+type, desc_gen)

  def rows_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.rows(r[0] if r is not None else None))

  app.add_url_rule('/'+type+'/<int:dataset_id>/rows','rows_'+type, rows_gen)

  def rowids_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.rowids(r[0] if r is not None else None))

  app.add_url_rule('/'+type+'/<int:dataset_id>/rowIds','rowids_'+type, rowids_gen)

  def data_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    formatter = resolve_formatter(type, flask.request.args.get('format','json'))
    return formatter(d, r, args=flask.request.args)

  app.add_url_rule('/'+type+'/<int:dataset_id>/data','data_'+type, data_gen)

def add_table_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'table')

def add_vector_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'vector')

def add_matrix_handler(app, dataset_getter):
  """
  add the handlers for handling a matrix
  :param app:
  :param dataset_getter:
  :return:
  """
  _add_handler(app, dataset_getter, 'matrix')

  def cols_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.cols(r[0] if r is not None else None))

  app.add_url_rule('/matrix/<int:dataset_id>/cols','cols_matrix', cols_matrix)

  def colids_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.colids(r[0] if r is not None else None))

  app.add_url_rule('/matrix/<int:dataset_id>/colIds','colids_matrix', colids_matrix)



