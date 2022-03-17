###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from logging.handlers import TimedRotatingFileHandler as Base


def phovea(registry):
  """
  extension points
  @param registry phovea registry
  register extension points
  :param registry:
  """
  registry.append('namespace', 'caleydo-dataset', 'phovea_server.dataset_api', {
      'namespace': '/api/dataset',
      'factory': 'create_dataset'
  })
  registry.append('namespace', 'caleydo-idtype', 'phovea_server.dataset_api', {
      'namespace': '/api/idtype',
      'factory': 'create_idtype'
  })
  registry.append('json-encoder', 'numpy', 'phovea_server.json_encoder')
  registry.append('json-encoder', 'set-encoder', 'phovea_server.set_encoder', {})

  registry.append('manager', 'mappingmanager', 'phovea_server.mapper', dict(singleton=True))

  registry.append('dataset-specific-handler', 'handler-graph', 'phovea_server.graph_api', {
      'datatype': 'graph',
      'factory': 'add_graph_handler'
  })
  registry.append('graph-formatter', 'formatter-json', 'phovea_server.graph_api', {
      'format': 'json',
      'factory': 'format_json'
  })
  registry.append('graph-parser', 'parser-json', 'phovea_server.graph_parser', {
      'format': 'json',
      'factory': 'parse_json'
  })
  registry.append('command', 'api', 'phovea_server.server', {'isDefault': True})


def phovea_config():
  """
  :return: file pointer to config file
  """
  from os import path
  here = path.abspath(path.dirname(__file__))
  config_file = path.join(here, 'config.json')
  return config_file if path.exists(config_file) else None


def _ensure_exists(filename):
  import os
  # ensure directory exists
  d = os.path.dirname(filename)
  if not os.path.exists(d):
    os.makedirs(d)
  return filename


class TimedRotatingFileHandler(Base):
  def __init__(self, filename, *args, **kwargs):
    super(TimedRotatingFileHandler, self).__init__(_ensure_exists(filename), *args, **kwargs)
