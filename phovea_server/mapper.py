###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object, set
from .plugin import list as list_plugin
from itertools import izip
import logging

_log = logging.getLogger(__name__)


class MappingManager(object):
  """
  assigns ids to object using a redis database
  """

  def __init__(self):
    self.mappers = {}
    for plugin in list_plugin('mapping_provider'):
      _log.info('loading mapping provider: %s', plugin.id)
      provider = plugin.load().factory()
      for (from_idtype, to_idtype, mapper) in provider:
        from_mappings = self.mappers.get(from_idtype, {})
        self.mappers[from_idtype] = from_mappings
        to_mappings = from_mappings.get(to_idtype, [])
        from_mappings[to_idtype] = to_mappings
        to_mappings.append(mapper)

  def known_idtypes(self):
    """
    returns a set of a all known id types in this mapping graph
    :return:
    """
    s = set()
    for from_, v in self.mappers.items():
      s.add(from_)
      for to_ in v.keys():
        s.add(to_)
    return s

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
    r = [[] for _ in ids]
    rset = [set() for _ in ids]
    for mapper in to_mappings:
      mapped_ids = mapper(ids)
      for mapped_id, rlist, rhash in izip(mapped_ids, r, rset):
        for id in mapped_id:
          if id not in rhash:
            rlist.append(id)
            rhash.add(id)
    return r

  def search(self, from_idtype, to_idtype, query, max_results=None):
    """
    searches for matches in the names of the given idtype
    :param query:
    :param max_results
    :return:
    """
    from_mappings = self.mappers.get(from_idtype, {})
    to_mappings = from_mappings.get(to_idtype, [])
    to_mappings = [m for m in to_mappings if hasattr(m, 'search')]

    if not to_mappings:
      _log.warn('cannot find mapping from %s to %s', from_idtype, to_idtype)
      return []

    if len(to_mappings) == 1:
      # single mapping no need for merging
      return to_mappings[0].search(query, max_results)

    rset = set()
    for mapper in to_mappings:
      results = mapper.serach(query, max_results)
      for r in results:
        rset.add(r)
    return list(rset)


def create():
  return MappingManager()
