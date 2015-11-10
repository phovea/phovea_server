__author__ = 'Samuel Gratzl'

class MemoryIDAssigner(object):
  def __init__(self):
    self._idsmapping = {}

  def unmap(self, uids, idtype):
    if idtype not in self._idsmapping:
      return [None] * len(uids)
    cache = self._idsmapping[idtype]
    def lookup(id):
      for k,v in cache.iteritems():
        if v == id:
          return v
      return None
    return map(lookup, uids)

  def __call__(self, ids, idtype):
    """
     return the integer index ids for the given ids in the given idtype
    """
    if idtype not in self._idsmapping:
      self._idsmapping[idtype] = { id: i for i,id in enumerate(ids) }
      #1 to 1 mapping
      return range(len(ids))

    cache = self._idsmapping[idtype]
    def add(id) :
      i = cache.get(id, -1)
      if i < 0: #not yet part of
        i = len(cache)
        cache[id] = i
      return i
    return [ add(id) for id in ids]

_assigner = MemoryIDAssigner()

def create():
  return _assigner
