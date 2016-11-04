###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from __future__ import print_function
from .server import run, application


if __name__ == '__main__':
  print('run as standalone version')
  run()
else:
  print('run as embedded version: %s', application)
