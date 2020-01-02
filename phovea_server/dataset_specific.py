###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import zip
from builtins import str
from . import ns
from . import range as ranges
from .util import jsonify
from .plugin import list as list_plugins
import numpy as np
from PIL import Image


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
    if isinstance(v, str):
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


def _hex_to_rgb(hex):
  hex = hex.lstrip('#')
  # hlen = len(hex)
  hlen = 6  # assume 6-digits HEX value! Does not work with 3- or 8-digits HEX values!
  return tuple(int(hex[i:i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))


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
  colors = [_hex_to_rgb(c) for c in colors]
  return ColorPalette(*colors).as_palette()


def _set_missing_values(img, arr, color):
  import numpy as np
  locs = np.transpose(np.where(np.isnan(arr)))
  if locs.size > 0:
    img = img.convert('RGB')
    for loc in locs:
      img.putpixel((loc[1], loc[0]), color)
  return img

# bytescale and scipy.misc.toimage() were completely removed -> the original functions are ported here

_errstr = "Mode is unknown or incompatible with input array shape."


def bytescale(data, cmin=None, cmax=None, high=255, low=0):
    """
    Byte scales an array (image).
    Byte scaling means converting the input image to uint8 dtype and scaling
    the range to ``(low, high)`` (default 0-255).
    If the input image already has dtype uint8, no scaling is done.
    This function is only available if Python Imaging Library (PIL) is installed.
    Parameters
    ----------
    data : ndarray
        PIL image data array.
    cmin : scalar, optional
        Bias scaling of small values. Default is ``data.min()``.
    cmax : scalar, optional
        Bias scaling of large values. Default is ``data.max()``.
    high : scalar, optional
        Scale max value to `high`.  Default is 255.
    low : scalar, optional
        Scale min value to `low`.  Default is 0.
    Returns
    -------
    img_array : uint8 ndarray
        The byte-scaled array.
    """
    if data.dtype == np.uint8:
        return data

    if high > 255:
        raise ValueError("`high` should be less than or equal to 255.")
    if low < 0:
        raise ValueError("`low` should be greater than or equal to 0.")
    if high < low:
        raise ValueError("`high` should be greater than or equal to `low`.")

    if cmin is None:
        cmin = data.min()
    if cmax is None:
        cmax = data.max()

    cscale = cmax - cmin
    if cscale < 0:
        raise ValueError("`cmax` should be larger than `cmin`.")
    elif cscale == 0:
        cscale = 1

    scale = float(high - low) / cscale
    bytedata = (data - cmin) * scale + low
    return (bytedata.clip(low, high) + 0.5).astype(np.uint8)


def toimage(arr, high=255, low=0, cmin=None, cmax=None, pal=None,
            mode=None, channel_axis=None):
    """Takes a numpy array and returns a PIL image.
    This function is only available if Python Imaging Library (PIL) is installed.
    The mode of the PIL image depends on the array shape and the `pal` and
    `mode` keywords.
    For 2-D arrays, if `pal` is a valid (N,3) byte-array giving the RGB values
    (from 0 to 255) then ``mode='P'``, otherwise ``mode='L'``, unless mode
    is given as 'F' or 'I' in which case a float and/or integer array is made.
    .. warning::
        This function uses `bytescale` under the hood to rescale images to use
        the full (0, 255) range if ``mode`` is one of ``None, 'L', 'P', 'l'``.
        It will also cast data for 2-D images to ``uint32`` for ``mode=None``
        (which is the default).
    Notes
    -----
    For 3-D arrays, the `channel_axis` argument tells which dimension of the
    array holds the channel data.
    For 3-D arrays if one of the dimensions is 3, the mode is 'RGB'
    by default or 'YCbCr' if selected.
    The numpy array must be either 2 dimensional or 3 dimensional.
    """
    data = np.asarray(arr)
    if np.iscomplexobj(data):
        raise ValueError("Cannot convert a complex-valued array.")
    shape = list(data.shape)
    valid = len(shape) == 2 or ((len(shape) == 3) and
                                ((3 in shape) or (4 in shape)))
    if not valid:
        raise ValueError("'arr' does not have a suitable array shape for "
                         "any mode.")
    if len(shape) == 2:
        shape = (shape[1], shape[0])  # columns show up first
        if mode == 'F':
            data32 = data.astype(np.float32)
            image = Image.frombytes(mode, shape, data32.tostring())
            return image
        if mode in [None, 'L', 'P']:
            bytedata = bytescale(data, high=high, low=low,
                                 cmin=cmin, cmax=cmax)
            image = Image.frombytes('L', shape, bytedata.tostring())
            if pal is not None:
                image.putpalette(np.asarray(pal, dtype=np.uint8).tostring())
                # Becomes a mode='P' automatically.
            elif mode == 'P':  # default gray-scale
                pal = (np.arange(0, 256, 1, dtype=np.uint8)[:, np.newaxis] *
                       np.ones((3,), dtype=np.uint8)[np.newaxis, :])
                image.putpalette(np.asarray(pal, dtype=np.uint8).tostring())
            return image
        if mode == '1':  # high input gives threshold for 1
            bytedata = (data > high)
            image = Image.frombytes('1', shape, bytedata.tostring())
            return image
        if cmin is None:
            cmin = np.amin(np.ravel(data))
        if cmax is None:
            cmax = np.amax(np.ravel(data))
        data = (data*1.0 - cmin)*(high - low)/(cmax - cmin) + low
        if mode == 'I':
            data32 = data.astype(np.uint32)
            image = Image.frombytes(mode, shape, data32.tostring())
        else:
            raise ValueError(_errstr)
        return image

    # if here then 3-d array with a 3 or a 4 in the shape length.
    # Check for 3 in datacube shape --- 'RGB' or 'YCbCr'
    if channel_axis is None:
        if (3 in shape):
            ca = np.flatnonzero(np.asarray(shape) == 3)[0]
        else:
            ca = np.flatnonzero(np.asarray(shape) == 4)
            if len(ca):
                ca = ca[0]
            else:
                raise ValueError("Could not find channel dimension.")
    else:
        ca = channel_axis

    numch = shape[ca]
    if numch not in [3, 4]:
        raise ValueError("Channel axis dimension is not valid.")

    bytedata = bytescale(data, high=high, low=low, cmin=cmin, cmax=cmax)
    if ca == 2:
        strdata = bytedata.tostring()
        shape = (shape[1], shape[0])
    elif ca == 1:
        strdata = np.transpose(bytedata, (0, 2, 1)).tostring()
        shape = (shape[2], shape[0])
    elif ca == 0:
        strdata = np.transpose(bytedata, (1, 2, 0)).tostring()
        shape = (shape[2], shape[1])
    if mode is None:
        if numch == 3:
            mode = 'RGB'
        else:
            mode = 'RGBA'

    if mode not in ['RGB', 'RGBA', 'YCbCr', 'CMYK']:
        raise ValueError(_errstr)

    if mode in ['RGB', 'YCbCr']:
        if numch != 3:
            raise ValueError("Invalid array shape for mode.")
    if mode in ['RGBA', 'CMYK']:
        if numch != 4:
            raise ValueError("Invalid array shape for mode.")

    # Here we know data and mode is correct
    image = Image.frombytes(mode, shape, strdata)
    return image

# end of ported functions


def format_image(dataset, range, args):
  format = args.get('format', 'png')

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
  img = toimage(d, cmin=cmin, cmax=cmax, pal=_color_palette(args.get('format_palette', None)))

  # convert to real RGB image
  # inject missing values
  img = _set_missing_values(img, d, _hex_to_rgb(args.get('format_missing'[0], '#d400c2')))

  if 'format_w' in args:
    width = int(args.get('format_w'))
    wpercent = width // float(img.size[0])
    height = int(args.get('format_h', (float(img.size[1]) * float(wpercent))))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)
  elif 'format_h' in args:
    height = int(args.get('format_h'))
    hpercent = height // float(img.size[1])
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
    r = asrange(ns.request.values.get('range', None))
    formatter = resolve_formatter(type, ns.request.values.get('format', 'json'))
    return formatter(d, r, args=ns.request.values)

  app.add_url_rule('/' + type + '/<dataset_id>/data', 'data_' + type, ns.etag(data_gen), methods=['GET', 'POST'])


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
