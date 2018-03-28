###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from builtins import object
from decimal import Decimal


class JSONDecimalEncoder(object):
  def __contains__(self, obj):
    if isinstance(obj, Decimal):
      return True
    return False

  def __call__(self, obj, base_encoder):
    return str(obj)


n = JSONDecimalEncoder()


def create():
  return n
