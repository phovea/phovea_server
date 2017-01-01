###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from .swagger import to_json
from .dataset import iter, get, add, remove
from .dataset_api_util import on_invalid_id, to_query, on_value_error, to_range, from_json


def list_dataset(limit=-1, id=None, name=None, fqname=None, type=None):
  query = to_query(id=id, name=name, fqname=fqname, type=type)
  data = [d.to_description() for d in iter() if query(d)]
  if 0 < limit < len(data):
    data = data[:limit]
  return data


def list_dataset_csv(limit, id=None, name=None, fqname=None, type=None, delimiter=';'):
  data = list_dataset(limit, id, name, fqname, type)

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
      yield delimiter.join([str(d['id']), d['name'], d['fqname'], d['type'], to_size(d.get('size', None)), to_json(d)])

  return ''.join(gen())


def list_dataset_tree(limit=-1, id=None, name=None, fqname=None, type=None):
  data = list_dataset(limit, id, name, fqname, type)
  r = dict(name='/')
  for d in data:
    levels = d['fqname'].split('/')
    act = r
    for level in levels:
      if level not in act:
        act[level] = dict()
      act = act[level]
    act[d['name']] = d
  return r


def upload_dataset(desc, file=None):
  desc = from_json(desc)
  try:
    # first choose the provider to handle the upload
    r = add(desc, file, desc.get('id', None))
    if r:
      return r.to_description()
    # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def get_dataset(datasetid, range=None):
  range = to_range(range)
  d = get(datasetid)
  if d is None:
    return on_invalid_id(datasetid)
  return d.asjson()


def put_dataset(datasetid, desc, file=None):
  desc = from_json(desc)
  try:
    old = get(datasetid)
    if old is None:
      desc['id'] = datasetid
      return upload_dataset(desc, file)
    r = old.update(desc, file)
    if r:
      return old.to_description()
    # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def post_dataset(datasetid, desc, file=None):
  desc = from_json(desc)
  try:
    old = get(datasetid)
    if old is None:
      return on_invalid_id(datasetid)
    r = old.modify(desc, file)
    if r:
      return old.to_description()
      # invalid upload
    return 'invalid upload', 400
  except ValueError as e:
    return on_value_error(e)


def delete_dataset(datasetid):
  dataset = get(datasetid)
  if dataset is None:
    return on_invalid_id(datasetid)
  r = remove(datasetid)
  if r:
    return dict(state='success', msg='Successfully deleted dataset ' + datasetid, id=datasetid)
  return 'invalid request', 400


def get_dataset_desc(datasetid):
  d = get(datasetid)
  if d is None:
    return on_invalid_id(datasetid)
  return d.to_description()
