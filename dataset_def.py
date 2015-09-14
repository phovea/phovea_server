__author__ = 'Samuel Gratzl'

class ADataSetEntry(object):
  """
  A basic dataset entry
  """
  def __init__(self, name, project, type, id = None):
    """
    constructor for a new dataset
    :param name:
    :param project: the parent/folder of this dataset
    :param type: the type of this dataset
    :param id: optional the id to use
    """
    self.name = name
    self.fqname = project + '/'+ name
    self.type = type
    import caleydo_server.util
    self.id = id if id is not None else caleydo_server.util.fix_id(self.fqname)

  def idtypes(self):
    """
    :return: the list of all idtypes as string array
    """
    return []

  def to_description(self):
    """
    :return: a dictionary describing this dataset in a client understandable format
    """
    return dict(type=self.type,
                name=self.name,
                id=self.id,
                fqname=self.fqname)

  def to_idtype_descriptions(self):
    """
    list of a all idtypes of this dataset
    :return:
    """
    def to_desc(t):
      return dict(id=t, name=t, names=t + 's')

    return map(to_desc, self.idtypes())

  def update(self, args, files):
    """
    updates this dataset with the new data
    :param args: data dict
    :param files: list of FileStorage files
    :return: boolean whether the operation was successful
    """
    return False

  def modify(self, args, files):
    """
    modifies this dataset with the given arguments
    :param args: data dict
    :param files: list of FileStorage files
    :return: boolean whether the operation was successful
    """
    return False

  def remove(self):
    """
    removes itself
    :return: boolean whether it was successfully removed
    """
    return False

  def asjson(self, range=None):
    """
    converts this dataset to a json compatible format
    :param range: optional sub range to deliver
    :return: a json compatible dataset representation
    """
    return dict()


class ADataSetProvider(object):

  def __len__(self):
    return 0
  def __iter__(self):
    return iter([])

  def __getitem__(self, dataset_id):
    """
    get a specific dataset item by id
    :param dataset_id:
    :return: the dataset or None
    """
    for elem in self:
      if elem.id == dataset_id:
        return elem
    return None

  def remove(self, entry):
    return False

  def upload(self, data, files, id=None):
    """
    adds a new dataset to this provider
    :param data: the description data dict object
    :param files: a list of FileStorage files containing data files
    :param id: optional unique id of the newly created dataset
    :return: None if the element can't be uploaded else the dataset
    """
    return None