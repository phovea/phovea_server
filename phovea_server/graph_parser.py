###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


def parse_json(args, files):
  if 'desc' in args:
    import json
    args = json.loads(args['desc'])
  if 'nodes' not in args:
    args['nodes'] = []
  if 'edges' not in args:
    args['edges'] = []
  return args
