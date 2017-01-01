from .util import to_json as to_json_impl


class AbortException(Exception):
  def __init__(self, msg='internal exception occurred', status_code=500):
    Exception.__init__(self, msg)
    self.status_code = status_code


def abort(msg, status_code):
  import flask
  return flask.abort(status_code, msg)
  # raise AbortException(msg, status_code)


def to_json(*args, **kwargs):
  return to_json_impl(*args, **kwargs)
