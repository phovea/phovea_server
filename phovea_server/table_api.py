###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from .dataset_api_util import dataset_getter, to_range
from .swagger import to_json, abort
import range as ranges


def _get_dataset(datasetid):
  return dataset_getter(datasetid, 'table')


def get_table(datasetid):
  d = _get_dataset(datasetid)
  return d.to_description()


def get_table_data(datasetid, range=None, pretty_print=False):
  range = to_range(range)
  d = _get_dataset(datasetid)
  d = d.asjson(range)
  if pretty_print:
    return to_json(d, indent=' ', allow_nan=False)
  return to_json(d, allow_nan=False)


def to_csv(dataset, param, range, include_rows=False, delimiter=';'):
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
    header = delimiter.join([d.name for d in dataset.columns])

    d = dataset.aslist(param)

    if include_rows:
      rows = dataset.rows(range[0] if range is not None else None)
      yield dataset.idtype
      yield delimiter

    yield header
    yield '\n'

    if include_rows:
      # extend with the row ids
      for row, line in itertools.izip(rows, d):
        yield row
        yield delimiter
        l = (to_str(line[d.name] for d in dataset.columns))
        yield delimiter.join(l)
        yield '\n'
    else:
      for line in d:
        l = (to_str(line[d.name] for d in dataset.columns))
        yield delimiter.join(l)
        yield '\n'

  return ''.join(gen())


def get_table_data_csv(datasetid, range=None, include_rows=False, delimiter=';'):
  range = to_range(range)
  dataset = _get_dataset(datasetid)
  return to_csv(dataset, range, range, include_rows, delimiter)


def get_table_rows(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return d.rows(range[0] if range is not None else None)


def get_table_row_ids(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  ids = d.rowids(range[0] if range is not None else None)
  return str(ranges.from_list(list(ids)))


def get_table_raw(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return list(d.aslist(range))


def get_table_column(datasetid, column, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  for col in d.columns:
    if col.name == column:
      return list(col.aslist(range))
  return 'column not found', 404


def _find_view(datasetid, viewname):
  d = _get_dataset(datasetid)
  if hasattr(d, 'views') and viewname in d.views:
    return d.views[viewname]
  abort('view not found', 404)


def get_table_view(datasetid, viewname, pretty_print, **kwargs):
  view = _find_view(datasetid, viewname)
  d = view.asjson(kwargs)
  if pretty_print:
    return to_json(d, indent=' ', allow_nan=False)
  return to_json(d, allow_nan=False)


def get_table_view_data_csv(datasetid, viewname, include_rows=False, delimiter=';', **kwargs):
  view = _find_view(datasetid, viewname)
  return to_csv(view, kwargs, None, include_rows, delimiter)


def get_table_view_rows(datasetid, viewname, **kwargs):
  view = _find_view(datasetid, viewname)
  return view.rows(kwargs)


def get_table_view_row_ids(datasetid, viewname, **kwargs):
  view = _find_view(datasetid, viewname)
  ids = view.rowids(kwargs)
  str(ranges.from_list(list(ids)))


def get_table_view_raw(datasetid, viewname, **kwargs):
  view = _find_view(datasetid, viewname)
  return list(view.aslist(kwargs))
