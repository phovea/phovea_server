###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from phovea_server import launch

if __name__ == '__main__':
  launch.run()
else:
  application = launch.create_embedded()
  print('run as embedded version: %s', application)
