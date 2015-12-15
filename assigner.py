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
          return k
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


class DBIDAssigner(object):
  def __init__(self):
    import anydbm
    import caleydo_server.config
    self._db = anydbm.open(caleydo_server.config.get('caleydo_server.dataDir')+'/mapping.dbm','c')

  @staticmethod
  def to_forward_key(idtype, identifier):
    return idtype + '2id.' + str(identifier)

  @staticmethod
  def to_backward_key(idtype, id):
    return 'id2' + idtype + '.' + str(id)

  def unmap(self, uids, idtype):
    def lookup(id):
      key = self.to_backward_key(idtype, id)
      return self._db.get(key, None)
    return map(lookup, uids)

  def __call__(self, ids, idtype):
    """
     return the integer index ids for the given ids in the given idtype
    """

    def add(id) :
      key = self.to_forward_key(idtype, id)
      i = int(self._db.get(key, '-1'))
      if i < 0: #not yet part of
        i = int(self._db.get(idtype,'-1'))+1
        self._db[key] = str(i)
        self._db[self.to_backward_key(idtype, i)] = str(id)
        self._db[idtype] = str(i)
      return i
    return map(add, ids)

_assigner = DBIDAssigner()

def create():
  return _assigner
