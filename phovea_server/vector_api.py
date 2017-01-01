###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from .dataset_api_util import dataset_getter, to_range
from .swagger import to_json
import range as ranges


def _get_dataset(datasetid):
  return dataset_getter(datasetid, 'vector')


def get_vector(datasetid):
  d = _get_dataset(datasetid)
  return d.to_description()


def get_vector_data(datasetid, range=None, pretty_print=False):
  range = to_range(range)
  d = _get_dataset(datasetid)
  d = d.asjson(range)
  if pretty_print:
    return to_json(d, indent=' ', allow_nan=False)
  return to_json(d, allow_nan=False)


def get_vector_data_csv(datasetid, range=None, include_rows=False, delimiter=';'):
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
    d = dataset.aslist(range)

    if include_rows:
      rows = dataset.rows(range[0] if range is not None else None)
      yield dataset.idtype
      yield delimiter
      yield '\n'
      # extend with the row ids
      for row, value in itertools.izip(rows, d):
        yield row
        yield delimiter
        yield to_str(value)
        yield '\n'
    else:
      yield 'Value\n'
      for value in d:
        yield to_str(value)
        yield '\n'

  return ''.join(gen())


def get_vector_rows(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return d.rows(range[0] if range is not None else None)


def get_vector_row_ids(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  ids = d.rowids(range[0] if range is not None else None)
  str(ranges.from_list(list(ids)))


def get_vector_raw(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return list(d.aslist(range))


def get_vector_hist(datasetid, range=None, bins=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  import numpy as np
  data = d.asnumpy(range)
  bins = int(bins or np.sqrt(len(data)))
  hist, bin_edges = np.histogram(data, bins=bins, range=d.range)
  return list(hist)
