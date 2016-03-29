__author__ = 'Samuel Gratzl'

import flask
import range as ranges
from caleydo_server.util import jsonify
import caleydo_server.plugin

def asrange(r):
  if r is None or r == '':
    return None
  return ranges.parse(r)

def format_json(dataset, range, args):
  d = dataset.asjson(range)
  if bool(args.get('f_pretty_print', False)):
    return jsonify(d, indent=' ', allow_nan=False)
  return jsonify(d, allow_nan=False)

def format_csv(dataset, range, args):
  include_rows = bool(args.get('f_rows', False))
  include_cols = bool(args.get('f_cols', False))
  delimiter = args.get('f_delimiter',';')

  import itertools
  import numpy as np
  import numpy.ma as ma

  def to_str(v):
    if isinstance(v, basestring):
      return v
    if np.isnan(v) or ma.is_masked(v):
      return ''
    return str(v)

  def gen():
    if include_cols and dataset.type == 'matrix':
      cols = dataset.cols(range[1] if range is not None else None)
      header = delimiter.join(cols)
    elif dataset.type == 'table':
      header = delimiter.join([d.name for d in dataset.columns])
    else:
      header = ''

    d = dataset.aslist(range)

    if include_rows:
      rows = dataset.rows(range[0] if range is not None else None)
      yield dataset.idtype if dataset.type == 'table' else dataset.rowtype
      yield delimiter

    yield header
    yield '\n'

    if include_rows:
      #extend with the row ids
      for row, line in itertools.izip(rows, d):
        yield row
        yield delimiter
        yield delimiter.join(map(to_str, line))
        yield '\n'
    else:
      for line in d:
        yield delimiter.join(map(to_str, line))
        yield '\n'

  return flask.Response(gen(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename='+dataset.name+'.csv'})

def _color_palette(arg):
  if arg is None:
    return None
  if arg == 'blue_white_red':
    from .colors import blue_white_red
    return blue_white_red.as_palette()
  elif arg == 'white_red':
    from .colors import white_red
    return white_red.as_palette()
  return None

def format_image(dataset, range, args):
  format = args.get('format','png')

  import scipy.misc
  import io
  import numpy as np

  #TODO set a palette to specify colors instead of gray scales
  #how to interpolate / sample colors - which space?
  minmax = dataset.range
  cmin = float(args.get('format_min',minmax[0]))
  cmax = float(args.get('format_max',minmax[1]))
  d = np.array(dataset.aslist(range))
  if d.ndim == 1:
    d = d.reshape((1,d.shape[0]))
  img = scipy.misc.toimage(d, cmin=cmin, cmax=cmax, pal = _color_palette(args.get('format_palette', None)))

  if 'format_w' in args:
    width = int(args.get('format_w'))
    wpercent = (width/float(img.size[0]))
    height = int(args.get('format_h', (float(img.size[1])*float(wpercent))))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)
  elif 'format_h' in args:
    height = int(args.get('format_h'))
    hpercent = (height/float(img.size[1]))
    width = int(float(img.size[0])*float(hpercent))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)

  if args.get('format_transpose', False):
    from PIL.Image import ROTATE_90
    img = img.transpose(ROTATE_90)

  b = io.BytesIO()
  img.save(b, format=format)
  b.seek(0)
  return flask.send_file(b, mimetype='image/'+format.replace('jpg','jpeg'))

def resolve_formatter(type, format):
  for p in caleydo_server.plugin.list(type+'-formatter'):
    if p.format == format:
      return p.load()
  flask.abort(400,'unknown format "{0}" possible formats are: {1}'.format(format, ','.join((p.format for p in caleydo_server.plugin.list(type+'-formatter')))))

def _add_handler(app, dataset_getter, type):
  def desc_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    return jsonify(d.to_description())

  app.add_url_rule('/'+type+'/<dataset_id>','desc_'+type, desc_gen)

  def rows_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.rows(r[0] if r is not None else None))

  app.add_url_rule('/'+type+'/<dataset_id>/rows','rows_'+type, rows_gen)

  def rowids_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    ids = d.rowids(r[0] if r is not None else None)
    return jsonify(str(ranges.from_list(list(ids))))

  app.add_url_rule('/'+type+'/<dataset_id>/rowIds','rowids_'+type, rowids_gen)

  def raw_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    return jsonify(d.aslist(r), allow_nan=False)

  app.add_url_rule('/'+type+'/<dataset_id>/raw','raw_'+type, raw_gen)

  def data_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(flask.request.args.get('range',None))
    formatter = resolve_formatter(type, flask.request.args.get('format','json'))
    return formatter(d, r, args=flask.request.args)

  app.add_url_rule('/'+type+'/<dataset_id>/data','data_'+type, data_gen)

def add_table_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'table')

def add_vector_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'vector')

  def hist_vector(dataset_id):
    d = dataset_getter(dataset_id, 'vector')
    r = asrange(flask.request.args.get('range',None))
    import numpy as np
    data = d.asnumpy(r)
    hist, bin_edges = np.histogram(data, bins=int(flask.request.args.get('bins',np.sqrt(len(data)))), range=d.range)
    return jsonify(hist)

  app.add_url_rule('/vector/<dataset_id>/hist','hist_vector', hist_vector)


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

  app.add_url_rule('/matrix/<dataset_id>/cols','cols_matrix', cols_matrix)

  def colids_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(flask.request.args.get('range',None))
    ids = d.colids(r[0] if r is not None else None)
    return jsonify(str(ranges.from_list(list(ids))))

  app.add_url_rule('/matrix/<dataset_id>/colIds','colids_matrix', colids_matrix)

  def hist_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(flask.request.args.get('range',None))
    data = d.asnumpy(r)
    import numpy as np
    hist, bin_edges = np.histogram(data, bins=int(flask.request.args.get('bins',np.sqrt(len(data)))), range=d.range)
    return jsonify(hist)

  app.add_url_rule('/matrix/<dataset_id>/hist','hist_matrix', hist_matrix)



