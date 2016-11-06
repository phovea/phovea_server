###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from __future__ import print_function
from . import ns
import os.path
import datetime
from .util import jsonify

last_deployment = ns.Namespace(__name__)


def modification_date(filename):
  t = os.path.getmtime(filename)
  return datetime.datetime.fromtimestamp(t)


@last_deployment.route('/', methods=['GET'])
def _last_deployment():
  """
   Reads the modification date of the caleydo_web_container/package.json
   OR as fallback (for builded bundles) the caleydo_web_container/registry.json.
  """
  path = os.path.normpath(os.path.join(os.getcwd(), 'package.json'))

  date = modification_date(path)
  print('modification date of {} = {}'.format(path, date))
  return jsonify(dict(timestamp=date))


def create_last_deployment():
  return last_deployment
