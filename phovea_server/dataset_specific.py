###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from __future__ import division
from __future__ import absolute_import
from builtins import zip
from builtins import str
from past.builtins import basestring
from . import ns
from . import range as ranges
from .util import jsonify
from .plugin import list as list_plugins


def asrange(r):
  if r is None or r == '':
    return None
  return ranges.parse(r)


def format_json(dataset, range, args):
  d = dataset.asjson(range)
  if bool(args.get('f_pretty_print', False)):
    return jsonify(d, indent=' ', allow_nan=False)
  return jsonify(d, allow_nan=False)


def format_csv(dataset, range, args):  # noqa
  include_rows = bool(args.get('f_rows', False))
  include_cols = bool(args.get('f_cols', False))
  delimiter = args.get('f_delimiter', ';')

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
      # extend with the row ids
      for row, line in zip(rows, d):
        yield row
        yield delimiter
        l = [to_str(v) for v in line] if dataset.type == 'matrix' else (to_str(line[d.name] for d in dataset.columns))
        yield delimiter.join(l)
        yield '\n'
    else:
      for line in d:
        l = [to_str(v) for v in line] if dataset.type == 'matrix' else (to_str(line[d.name] for d in dataset.columns))
        yield delimiter.join(l)
        yield '\n'

  return ns.Response(gen(), mimetype='text/csv',
                     headers={'Content-Disposition': 'attachment;filename=' + dataset.name + '.csv'})


def _parse_color(hex):
  import struct
  str = hex[1:] if hex.startswith('#') else hex
  return struct.unpack('BBB', str.decode('hex'))


def _color_palette(arg):
  if arg is None or arg == '':
    return None
  if arg == 'blue_white_red':
    from .colors import blue_white_red
    return blue_white_red.as_palette()
  elif arg == 'white_red':
    from .colors import white_red
    return white_red.as_palette()

  # generate color palette
  from .colors import ColorPalette
  colors = arg.split('-')
  colors = [_parse_color(c) for c in colors]
  return ColorPalette(*colors).as_palette()


def _set_missing_values(img, arr, color):
  import numpy as np
  locs = np.transpose(np.where(np.isnan(arr)))
  if locs.size > 0:
    img = img.convert('RGB')
    for loc in locs:
      img.putpixel((loc[1], loc[0]), color)
  return img


def format_image(dataset, range, args):
  format = args.get('format', 'png')

  import scipy.misc
  import io
  import numpy as np

  # TODO set a palette to specify colors instead of gray scales
  # how to interpolate / sample colors - which space?
  minmax = dataset.range
  cmin = float(args.get('format_min', minmax[0]))
  cmax = float(args.get('format_max', minmax[1]))
  d = np.array(dataset.aslist(range))
  if d.ndim == 1:
    d = d.reshape((1, d.shape[0]))
  img = scipy.misc.toimage(d, cmin=cmin, cmax=cmax, pal=_color_palette(args.get('format_palette', None)))

  # convert to real RGB image
  # inject missing values
  img = _set_missing_values(img, d, _parse_color(args.get('format_missing', '#d400c2')))

  if 'format_w' in args:
    width = int(args.get('format_w'))
    wpercent = width / float(img.size[0])
    height = int(args.get('format_h', (float(img.size[1]) * float(wpercent))))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)
  elif 'format_h' in args:
    height = int(args.get('format_h'))
    hpercent = height / float(img.size[1])
    width = int(float(img.size[0]) * float(hpercent))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)

  if args.get('format_transpose', False):
    from PIL.Image import ROTATE_90
    img = img.transpose(ROTATE_90)

  b = io.BytesIO()
  img.save(b, format=format)
  b.seek(0)
  return ns.send_file(b, mimetype='image/' + format.replace('jpg', 'jpeg'))


def resolve_formatter(type, format):
  for p in list_plugins(type + '-formatter'):
    if p.format == format:
      return p.load()
  desc = ','.join((p.format for p in list_plugins(type + '-formatter')))
  ns.abort(400, 'unknown format "{0}" possible formats are: {1}'.format(format, desc))


def _add_handler(app, dataset_getter, type):
  def desc_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    return jsonify(d.to_description())

  app.add_url_rule('/' + type + '/<dataset_id>', 'desc_' + type, ns.etag(desc_gen))

  def rows_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(ns.request.args.get('range', None))
    return jsonify(d.rows(r[0] if r is not None else None))

  app.add_url_rule('/' + type + '/<dataset_id>/rows', 'rows_' + type, ns.etag(rows_gen))

  def rowids_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(ns.request.args.get('range', None))
    ids = d.rowids(r[0] if r is not None else None)
    return jsonify(str(ranges.from_list(list(ids))))

  app.add_url_rule('/' + type + '/<dataset_id>/rowIds', 'rowids_' + type, ns.etag(rowids_gen))

  def raw_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(ns.request.args.get('range', None))
    return jsonify(d.aslist(r), allow_nan=False)

  app.add_url_rule('/' + type + '/<dataset_id>/raw', 'raw_' + type, ns.etag(raw_gen))

  def data_gen(dataset_id):
    d = dataset_getter(dataset_id, type)
    r = asrange(ns.request.args.get('range', None))
    formatter = resolve_formatter(type, ns.request.args.get('format', 'json'))
    return formatter(d, r, args=ns.request.args)

  app.add_url_rule('/' + type + '/<dataset_id>/data', 'data_' + type, ns.etag(data_gen))


def add_table_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'table')

  def find_view(dataset_id, view_name):
    d = dataset_getter(dataset_id, 'table')
    if hasattr(d, 'views') and view_name in d.views:
      view = d.views[view_name]
      args = ns.request.args.to_dict()
      return view, args
    ns.abort(404)

  def col_table(dataset_id, column):
    d = dataset_getter(dataset_id, 'table')
    r = asrange(ns.request.args.get('range', None))
    for col in d.columns:
      if col.name == column or col.dump().get('column', '') == column:
        return jsonify(col.aslist(r), allow_nan=False)
    ns.abort(404)

  def view_table(dataset_id, view_name):
    view, args = find_view(dataset_id, view_name)
    formatter = resolve_formatter('table', ns.request.args.get('format', 'json'))
    return formatter(view, args, args=ns.request.args)

  def view_raw_table(dataset_id, view_name):
    view, args = find_view(dataset_id, view_name)
    return jsonify(view.aslist(args), allow_nan=False)

  def view_rows_table(dataset_id, view_name):
    view, args = find_view(dataset_id, view_name)
    return jsonify(view.rows(args))

  def view_rowids_table(dataset_id, view_name):
    view, args = find_view(dataset_id, view_name)
    ids = view.rowids(args)
    return jsonify(str(ranges.from_list(list(ids))))

  app.add_url_rule('/table/<dataset_id>/col/<column>', 'col_table', ns.etag(col_table))

  app.add_url_rule('/table/<dataset_id>/view/<view_name>', 'view_table', ns.etag(view_table))
  app.add_url_rule('/table/<dataset_id>/view/<view_name>/raw', 'view_raw_table', ns.etag(view_raw_table))
  app.add_url_rule('/table/<dataset_id>/view/<view_name>/rows', 'view_rows_table', ns.etag(view_rows_table))
  app.add_url_rule('/table/<dataset_id>/view/<view_name>/rowIds', 'view_rowids_table', ns.etag(view_rowids_table))


def _stats_of(data):
  import numpy as np
  import scipy.stats
  return dict(median=np.nanmedian(data),
              q1=np.nanpercentile(data, 25),
              q3=np.nanpercentile(data, 75),
              min=np.nanmin(data),
              max=np.nanmax(data),
              sum=np.nansum(data),
              mean=np.nanmean(data),
              var=np.nanvar(data),
              sd=np.nanstd(data),
              n=len(data),
              nans=np.count_nonzero(np.isnan(data)),
              moment2=scipy.stats.moment(data, 2),
              moment3=scipy.stats.moment(data, 3),
              moment4=scipy.stats.moment(data, 4),
              kurtosis=scipy.stats.kurtosis(data),
              skewness=scipy.stats.skew(data))


def add_vector_handler(app, dataset_getter):
  _add_handler(app, dataset_getter, 'vector')

  def hist_vector(dataset_id):
    d = dataset_getter(dataset_id, 'vector')
    r = asrange(ns.request.args.get('range', None))
    import numpy as np
    data = d.asnumpy(r)
    hist, bin_edges = np.histogram(data, bins=int(ns.request.args.get('bins', np.sqrt(len(data)))), range=d.range)
    return jsonify(hist)

  def stats_vector(dataset_id):
    d = dataset_getter(dataset_id, 'vector')
    r = asrange(ns.request.args.get('range', None))
    data = d.asnumpy(r)
    return jsonify(_stats_of(data))

  app.add_url_rule('/vector/<dataset_id>/hist', 'hist_vector', ns.etag(hist_vector))
  app.add_url_rule('/vector/<dataset_id>/stats', 'stats_vector', ns.etag(stats_vector))


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
    r = asrange(ns.request.args.get('range', None))
    return jsonify(d.cols(r[0] if r is not None else None))

  app.add_url_rule('/matrix/<dataset_id>/cols', 'cols_matrix', ns.etag(cols_matrix))

  def colids_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(ns.request.args.get('range', None))
    ids = d.colids(r[0] if r is not None else None)
    return jsonify(str(ranges.from_list(list(ids))))

  app.add_url_rule('/matrix/<dataset_id>/colIds', 'colids_matrix', ns.etag(colids_matrix))

  def hist_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(ns.request.args.get('range', None))
    data = d.asnumpy(r)
    import numpy as np
    hist, bin_edges = np.histogram(data, bins=int(ns.request.args.get('bins', np.sqrt(len(data)))), range=d.range)
    return jsonify(hist)

  def stats_matrix(dataset_id):
    d = dataset_getter(dataset_id, 'matrix')
    r = asrange(ns.request.args.get('range', None))
    data = d.asnumpy(r)
    return jsonify(_stats_of(data.flat))

  app.add_url_rule('/matrix/<dataset_id>/hist', 'hist_matrix', ns.etag(hist_matrix))
  app.add_url_rule('/matrix/<dataset_id>/stats', 'stats_matrix', ns.etag(stats_matrix))
