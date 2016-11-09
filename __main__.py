###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################
from __future__ import print_function
from phovea_server.server import run, create_application


if __name__ == '__main__':
  print('run as standalone version')
  run()
else:
  application = create_application()
  print('run as embedded version: %s', application)
