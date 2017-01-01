###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from .ns import send_file
from .dataset_api_util import dataset_getter, to_range
from .swagger import to_json
import range as ranges


def _get_dataset(datasetid):
  return dataset_getter(datasetid, 'matrix')


def get_matrix(datasetid):
  d = _get_dataset(datasetid)
  return d.to_description()


def get_matrix_data(datasetid, range=None, pretty_print=False):
  range = to_range(range)
  d = _get_dataset(datasetid)
  d = d.asjson(range)
  if pretty_print:
    return to_json(d, indent=' ', allow_nan=False)
  return to_json(d, allow_nan=False)


def get_matrix_data_csv(datasetid, range=None, include_rows=False, include_cols=False, delimiter=';'):
  range = to_range(range)
  dataset = _get_dataset(datasetid)

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
    if include_cols:
      cols = dataset.cols(range[1] if range is not None else None)
      header = delimiter.join(cols)
    else:
      header = ''

    d = dataset.aslist(range)

    if include_rows:
      rows = dataset.rows(range[0] if range is not None else None)
      yield dataset.rowtype
      yield delimiter

    yield header
    yield '\n'

    if include_rows:
      # extend with the row ids
      for row, line in itertools.izip(rows, d):
        yield row
        yield delimiter
        l = map(to_str, line)
        yield delimiter.join(l)
        yield '\n'
    else:
      for line in d:
        l = map(to_str, line)
        yield delimiter.join(l)
        yield '\n'

  return ''.join(gen())


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


def get_matrix_data_png(datasetid, range=None, format='png', palette=False, min=None, max=None, width=None, height=None,
                        transpose=False):
  range = to_range(range)
  dataset = _get_dataset(datasetid)

  import scipy.misc
  import io
  import numpy as np

  # TODO set a palette to specify colors instead of gray scales
  # how to interpolate / sample colors - which space?
  minmax = dataset.range
  cmin = min if min is not None else minmax[0]
  cmax = min if max is not None else minmax[1]
  d = np.array(dataset.aslist(range))
  if d.ndim == 1:
    d = d.reshape((1, d.shape[0]))
  img = scipy.misc.toimage(d, cmin=cmin, cmax=cmax, pal=_color_palette(palette))

  if width is not None:
    wpercent = (width / float(img.size[0]))
    height = int(height if height is not None else (float(img.size[1]) * float(wpercent)))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)
  elif height is not None:
    hpercent = (height / float(img.size[1]))
    width = int(float(img.size[0]) * float(hpercent))
    from PIL.Image import NEAREST
    img = img.resize((width, height), NEAREST)

  if transpose:
    from PIL.Image import ROTATE_90
    img = img.transpose(ROTATE_90)

  b = io.BytesIO()
  img.save(b, format=format)
  b.seek(0)
  return send_file(b, mimetype='image/' + format.replace('jpg', 'jpeg'))


def get_matrix_data_jpg(datasetid, range=None, palette=False, min=None, max=None, width=None, height=None,
                        transpose=False):
  return get_matrix_data_png(datasetid, range, 'jpg', palette, min, max, width, height, transpose)


def get_matrix_rows(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return d.rows(range[0] if range is not None else None)


def get_matrix_row_ids(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  ids = d.rowids(range[0] if range is not None else None)
  str(ranges.from_list(list(ids)))


def get_matrix_cols(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return d.cols(range[0] if range is not None else None)


def get_matrix_col_ids(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  ids = d.colids(range[0] if range is not None else None)
  str(ranges.from_list(list(ids)))


def get_matrix_raw(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return to_json(d.aslist(range))


def get_matrix_hist(datasetid, range=None, bins=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  import numpy as np
  data = d.asnumpy(range)
  bins = int(bins or np.sqrt(len(data)))
  hist, bin_edges = np.histogram(data, bins=bins, range=d.range)
  return list(hist)
