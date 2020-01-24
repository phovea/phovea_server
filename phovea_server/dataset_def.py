###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from builtins import object
import abc
import numpy as np


def to_plural(s):
  if s[len(s) - 1] == 'y':
    return s[0:len(s) - 1] + 'ies'
  return s + 's'


def to_idtype_description(id):
  return dict(id=id, name=id, names=to_plural(id))


class ADataSetEntry(object, metaclass=abc.ABCMeta):
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

    return [to_idtype_description(t) for t in self.idtypes()]

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

  @abc.abstractmethod
  def asjson(self, range=None):
    """
    converts this dataset to a json compatible format
    :param range: optional sub range to deliver
    :return: a json compatible dataset representation
    """
    return dict()

  def can_read(self, user=None):
    from .security import can_read
    return can_read(self.to_description(), user)

  def can_write(self, user=None):
    from .security import can_write
    return can_write(self.to_description(), user)


class AStratification(ADataSetEntry, metaclass=abc.ABCMeta):
  """
  A basic dataset entry
  """

  def __init__(self, name, project, type, id=None):
    super(AStratification, self).__init__(name, project, type, id)
    self.idtype = 'Custom'

  @abc.abstractmethod
  def rows(self, range=None):
    return []

  @abc.abstractmethod
  def rowids(self, range=None):
    return []

  @abc.abstractmethod
  def groups(self):
    return []

  def idtypes(self):
    return [self.idtype]


class AMatrix(ADataSetEntry, metaclass=abc.ABCMeta):
  """
  A basic dataset entry
  """

  def __init__(self, name, project, type, id=None):
    super(AMatrix, self).__init__(name, project, type, id)
    self.rowtype = 'Custom'
    self.coltype = 'Custom'
    self.shape = [0, 0]
    self.value = 'string'

  @abc.abstractmethod
  def rows(self, range=None):
    return []

  @abc.abstractmethod
  def rowids(self, range=None):
    return []

  @abc.abstractmethod
  def cols(self, range=None):
    return []

  @abc.abstractmethod
  def colids(self, range=None):
    return []

  def aslist(self, range=None):
    return self.asnumpy(range).tolist()

  @abc.abstractmethod
  def asnumpy(self, range=None):
    return np.array([])

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    cols = self.cols(None if range is None else range[1])
    rowids = self.rowids(None if range is None else range[0])
    colids = self.colids(None if range is None else range[1])

    r = dict(data=arr, rows=rows, cols=cols, rowIds=rowids, colIds=colids)
    return r

  def idtypes(self):
    return [self.rowtype, self.coltype]


class AVector(ADataSetEntry, metaclass=abc.ABCMeta):
  """
  A basic dataset entry
  """

  def __init__(self, name, project, type, id=None):
    super(AVector, self).__init__(name, project, type, id)
    self.idtype = 'Custom'
    self.value = 'string'
    self.shape = [0]

  @abc.abstractmethod
  def rows(self, range=None):
    return []

  @abc.abstractmethod
  def rowids(self, range=None):
    return []

  def aslist(self, range=None):
    return self.asnumpy(range).tolist()

  @abc.abstractmethod
  def asnumpy(self, range=None):
    return np.array([])

  def asjson(self, range=None):
    arr = self.asnumpy(range)
    rows = self.rows(None if range is None else range[0])
    rowids = self.rowids(None if range is None else range[0])
    r = dict(data=arr, rows=rows, rowIds=rowids)

    return r

  def idtypes(self):
    return [self.idtype]


class AColumn(object, metaclass=abc.ABCMeta):
  def __init__(self, name, type):
    self.name = name
    self.type = type

  def aslist(self, range=None):
    return self.asnumpy(range).tolist()

  @abc.abstractmethod
  def asnumpy(self, range=None):
    return np.array([])

  @abc.abstractmethod
  def dump(self):
    return None


class ATable(ADataSetEntry, metaclass=abc.ABCMeta):
  """
  A basic dataset entry
  """

  def __init__(self, name, project, type, id=None):
    super(ATable, self).__init__(name, project, type, id)
    self.idtype = 'Custom'
    self.shape = [0, 0]
    self.columns = []

  @abc.abstractmethod
  def rows(self, range=None):
    return []

  @abc.abstractmethod
  def rowids(self, range=None):
    return []

  def aslist(self, range=None):
    data = self.aspandas(range)

    # if range is only one element, aspandas returns a Series, otherwise a Dataframe
    # to_dict('records') throws error on Series
    if range is not None and range.dims[0].size() == 1:
      return data.to_dict()

    return data.to_dict('records')

  @abc.abstractmethod
  def aspandas(self, range=None):
    import pandas as pd
    return pd.DataFrame()

  def asjson(self, range=None):
    arr = self.aslist(range)
    rows = self.rows(None if range is None else range[0])
    rowids = self.rowids(None if range is None else range[0])
    r = dict(data=arr, rows=rows, rowIds=rowids)

    return r

  def idtypes(self):
    return [self.idtype]


class ADataSetProvider(object, metaclass=abc.ABCMeta):
  def __len__(self):
    import itertools
    return itertools.count(self)

  @abc.abstractmethod
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
