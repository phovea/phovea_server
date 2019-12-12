###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from phovea_server import launch

# Test if the phovea_server runs as main program or is embedded (i.e., imported) in a different Python script
# See https://stackoverflow.com/a/419185 for further information.
if __name__ == '__main__':
  launch.run()
else:
  application = launch.create_embedded()
  print('run as embedded version: %s', application)
