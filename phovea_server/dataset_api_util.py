###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from . import plugin, range
from .swagger import abort
import logging
from .dataset import list_idtypes, get_idmanager, iter, get_mappingmanager, get, list_datasets as list_dataset_impl, \
  add, remove

_log = logging.getLogger(__name__)

def on_value_error(error):
  _log.error('ValueError: (' + str(error.message) + ')')
  _log.error(error)
  return '<strong>{2} - {0}</strong><pre>{1}</pre>'.format('ValueError', error.message, 500), 500

def on_invalid_id(datasetid):
  _log.info('requested invalid datasetid: '+str(datasetid))
  return 'invalid dataset id "' + str(datasetid) + '"', 404

def on_invalid_type(datasetid, dataset_type):
  return 'the given dataset "' + str(datasetid) + '" is not a ' + dataset_type, 400

def dataset_getter(datasetid, dataset_type):
  if isinstance(datasetid, int) and dataset_id < 0:
    return [d for d in list_datasets() if d.type == dataset_type]
  t = get(datasetid)
  if t is None:
    abort(*on_invalid_id(datasetid))
  if t.type != dataset_type:
    abort(*on_invalid_type(datasetid, dataset_type))
  return t

def to_query(**query):
  act_query = {k: v for k, v in query.iteritems()}
  if len(act_query) == 0:  # no query
    return lambda x: True
  import re

  def filter_elem(elem):
    return all((re.match(v, getattr(elem, k, '')) for k, v in act_query.iteritems()))

  return filter_elem
