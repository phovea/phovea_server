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
  registry.append('dataset-specific-handler', 'handler-table', 'phovea_server.dataset_specific', {
      'datatype': 'table',
      'factory': 'add_table_handler'
  })
  registry.append('dataset-specific-handler', 'handler-matrix', 'phovea_server.dataset_specific', {
      'datatype': 'matrix',
      'factory': 'add_matrix_handler'
  })
  registry.append('dataset-specific-handler', 'handler-vector', 'phovea_server.dataset_specific', {
      'datatype': 'vector',
      'factory': 'add_vector_handler'
  })
  registry.append('table-formatter', 'formatter-json', 'phovea_server.dataset_specific', {
      'format': 'json',
      'factory': 'format_json'
  })
  registry.append('table-formatter', 'formatter-csv', 'phovea_server.dataset_specific', {
      'format': 'csv',
      'factory': 'format_csv'
  })
  registry.append('matrix-formatter', 'formatter-json', 'phovea_server.dataset_specific', {
      'format': 'json',
      'factory': 'format_json'
  })
  registry.append('matrix-formatter', 'formatter-csv', 'phovea_server.dataset_specific', {
      'format': 'csv',
      'factory': 'format_csv'
  })
  registry.append('matrix-formatter', 'formatter-image', 'phovea_server.dataset_specific', {
      'format': 'png',
      'factory': 'format_image'
  })
  registry.append('matrix-formatter', 'formatter-image', 'phovea_server.dataset_specific', {
      'format': 'jpeg',
      'factory': 'format_image'
  })
  registry.append('matrix-formatter', 'formatter-image', 'phovea_server.dataset_specific', {
      'format': 'jpg',
      'factory': 'format_image'
  })
  registry.append('vector-formatter', 'formatter-json', 'phovea_server.dataset_specific', {
      'format': 'json',
      'factory': 'format_json'
  })
  registry.append('vector-formatter', 'formatter-csv', 'phovea_server.dataset_specific', {
      'format': 'csv',
      'factory': 'format_csv'
  })
  registry.append('dataset-provider', 'dataset-csv', 'phovea_server.dataset_csv')
  registry.append('json-encoder', 'numpy', 'phovea_server.json_encoder')
  registry.append('json-encoder', 'set-encoder', 'phovea_server.set_encoder', {})

  registry.append('manager', 'idmanager', 'phovea_server.assigner', dict(singleton=True))
  registry.append('manager', 'mappingmanager', 'phovea_server.mapper', dict(singleton=True))
  registry.append('mapping_provider', 'csv', 'phovea_server.mapping_csv')

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
