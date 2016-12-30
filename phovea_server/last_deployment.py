###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from __future__ import print_function
import os.path
import datetime

def modification_date(filename):
  t = os.path.getmtime(filename)
  return datetime.datetime.fromtimestamp(t)


def get_last_deployment():
  """
   Reads the modification date of the caleydo_web_container/package.json
   OR as fallback (for builded bundles) the caleydo_web_container/registry.json.
  """
  path = os.path.normpath(os.path.join(os.getcwd(), 'package.json'))

  date = modification_date(path)
  print('modification date of {} = {}'.format(path, date))
  return dict(timestamp=date)
