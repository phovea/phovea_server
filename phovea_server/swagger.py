
from .util import to_json

class AbortException(Exception):
  def __init__(self, msg = 'internal exception occurred', status_code = 500):
    Exception.__init__(self, msg)
    self.status_code = status_code

def abort(msg, status_code):
  raise AbortException(msg, status_code)


