###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object, set
import logging
import abc
from .plugin import list as list_plugin

_log = logging.getLogger(__name__)

class MappingManager(object):
  """
  assigns ids to object using a redis database
  """

  def __init__(self):
    self.mappers = {}
    for plugin in list_plugin('mapping_provider'):
      provider = plugin.load().factory()
      for (from_idtype, to_idtype, mapper) in provider:
        from_mappings = self.mappers.get(from_idtype, {})
        to_mappings = from_mappings.get(to_idtype, [])
        to_mappings.append(mapper)

  def can_map(self, from_idtype, to_idtype):
    from_mappings = self.mappers.get(from_idtype, {})
    return to_idtype in from_mappings

  def maps_to(self, from_idtype):
    from_mappings = self.mappers.get(from_idtype, {})
    return from_mappings.keys()

  def __call__(self, from_idtype, to_idtype, ids):
    from_mappings = self.mappers.get(from_idtype, {})
    to_mappings = from_mappings.get(to_idtype, [])
    if not to_mappings:
      _log.warn('cannot find mapping from %s to %s', from_idtype, to_idtype)
      return [None for _ in ids]

    if len(to_mappings) == 1:
      # single mapping no need for merging
      return to_mappings[0](ids)

    # two way to preserve the order of the results
    r = []
    rset = set()
    for mapper in to_mappings:
      ri = mapper(ids)
      for mapped in ri:
        if mapped not in rset:
          r.append(mapped)
          rset.add(mapped)
    return r


def create():
  return MappingManager()
