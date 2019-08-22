###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

import os
import sys
sys.path.insert(0, os.path.abspath('/phovea/phovea_server/phovea_server'))

if __name__ == '__main__':
  import launch
  launch.run()
else:
  import launch
  application = launch.create_embedded()
  print('run as embedded version: %s', application)
