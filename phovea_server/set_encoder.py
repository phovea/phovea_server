"""
This encoder is required to handle changes of data types in Python 3.7 by adding list() to set().
"""


class SetEncoder(object):
  def __contains__(self, obj):
    if isinstance(obj, set):
      return True
    return False

  def __call__(self, obj, base_encoder):
    if isinstance(obj, set):
      return list(obj)
    return None


encoder = SetEncoder()


def create():
  return encoder
