__author__ = 'Samuel Gratzl'

class ADataSetEntry(object):
  def __init__(self, name, project, type):
    self.name = name
    self.fqname = project + '/'+ name
    self.type = type
    import caleydo_server.util
    self.id = caleydo_server.util.fix_id(self.fqname)

  def idtypes(self):
    return []

  def to_description(self):
    return dict(type=self.type,
                name=self.name,
                id=self.id,
                fqname=self.fqname)

  def to_idtype_descriptions(self):
    def to_desc(t):
      return dict(id=t, name=t, names=t + 's')

    return map(to_desc, self.idtypes())

  def update(self, args, files):
    """
    can't update static csv files
    """
    return False

  def asjson(self, range=None):
    return dict()


class ADataSetProvider(object):

  def __len__(self):
    return 0
  def __iter__(self):
    return iter([])

  def __getitem__(self, dataset_id):
    for elem in self:
      if elem.id == dataset_id:
        return elem
    return None

  def upload(self, data, files, id=None):
    """

    :param data:
    :param files:
    :param id:
    :return:
    """
    return None