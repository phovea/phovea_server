###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


def to_plural(s):
  if s[len(s) - 1] == 'y':
    return s[0:len(s) - 1] + 'ies'
  return s + 's'


class ADataSetEntry(object):
  """
  A basic dataset entry
  """

  def __init__(self, name, project, type, id=None):
    """
    constructor for a new dataset
    :param name:
    :param project: the parent/folder of this dataset
    :param type: the type of this dataset
    :param id: optional the id to use
    """
    self.name = name
    self.fqname = project + '/' + name
    self.type = type
    from .util import fix_id
    self.id = id if id is not None else fix_id(self.fqname)

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
      return dict(id=t, name=t, names=to_plural(t))

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

    # specific api for vectors
    # idtype
    # shape
    # value
    # range
    # rows(range=None)
    # rowids(range=None)
    # aslist(range=None)
    # asnumpy(range=None)
    # specific api for matrices
    # rowtype
    # coltype
    # shape
    # value
    # range
    # rows(range=None)
    # rowids(range=None)
    # cols(range=None)
    # colids(range=None)
    # aslist(range=None)
    # asnumpy(range=None)
    # specific api for tables
    # idtype
    # columns
    # shape
    # rows(range=None)
    # rowids(range=None)
    # aslist(range=None)
    # aspandas(range=None)
    # specific api for stratifications
    # idtype
    # rows(range=None)
    # rowids(range=None)
    # groups()


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
