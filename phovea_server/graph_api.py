###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from .dataset_api_util import dataset_getter, to_range, from_json


def _get_dataset(datasetid):
  return dataset_getter(datasetid, 'graph')


def get_graph(datasetid):
  d = _get_dataset(datasetid)
  return d.to_description()


def get_graph_data(datasetid):
  d = _get_dataset(datasetid)
  return d.asjson()


def list_graph_node(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return [n.asjson() for n in d.nodes(range[0] if range is not None else None)]


def list_graph_edge(datasetid, range=None):
  range = to_range(range)
  d = _get_dataset(datasetid)
  return [n.asjson() for n in d.edges(range[0] if range is not None else None)]


def clear_graph_node(datasetid):
  d = _get_dataset(datasetid)
  if d.clear():
    return d.to_description()
  return 'unknown error', 400


def clear_graph_edge(datasetid):
  d = _get_dataset(datasetid)
  if d.clear():  # TODO will also clear everything
    return d.to_description()
  return 'unknown error', 400


def post_graph_node(datasetid, desc):
  desc = from_json(desc)
  d = _get_dataset(datasetid)
  if d.add_node(desc):
    return d.to_description()
  return 'cannot add node', 400


def post_graph_edge(datasetid, desc):
  desc = from_json(desc)
  d = _get_dataset(datasetid)
  if d.add_edge(desc):
    return d.to_description()
  return 'cannot add edge', 400


def get_graph_node(datasetid, nodeid):
  d = _get_dataset(datasetid)
  n = d.get_node(nodeid)
  if not n:
    return 'not found', 404
  return n.asjson()


def get_graph_edge(datasetid, edgeid):
  d = _get_dataset(datasetid)
  n = d.get_edge(edgeid)
  if not n:
    return 'not found', 404
  return n.asjson()


def delete_graph_node(datasetid, nodeid):
  d = _get_dataset(datasetid)
  if d.remove_node(nodeid):
    return d.to_description()
  return 'invalid', 400


def delete_graph_edge(datasetid, edgeid):
  d = _get_dataset(datasetid)
  if d.remove_edge(edgeid):
    return d.to_description()
  return 'invalid', 400


def put_graph_node(datasetid, nodeid, desc):
  desc = from_json(desc)
  desc['id'] = nodeid
  d = _get_dataset(datasetid)
  if d.update_node(desc):
    return d.to_description()
  return 'invalid', 400


def put_graph_edge(datasetid, edgeid, desc):
  desc = from_json(desc)
  desc['id'] = edgeid
  d = _get_dataset(datasetid)
  if d.update_edge(desc):
    return d.to_description()
  return 'invalid', 400
