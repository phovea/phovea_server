"""
This encoder is required to handle changes of data types in Python 3.7 by decoding bytes objects to strings and adding list() to set().
"""


class Python3Encoder(object):
  def __contains__(self, obj):
    if isinstance(obj, bytes):
      return True
    if isinstance(obj, set):
      return True
    return False

  def __call__(self, obj, base_encoder):
    if isinstance(obj, bytes):
      return obj.decode('utf-8')
    if isinstance(obj, set):
      return list(obj)
    return None


encoder = Python3Encoder()


def create():
  return encoder
