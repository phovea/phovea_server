"""
This encoder is required to handle changes of data types in Python 3.7 by converting NaN values to null.
"""
import math
import json
from flask import Response
import numpy as np
import pandas as pd

# https://stackoverflow.com/questions/47333227/pandas-valueerror-cannot-convert-float-nan-to-integer


class NaNEncoder(object):
  def __contains__(self, obj):
    if (isinstance(obj, float) and math.isnan(obj)):
      return True
    elif isinstance(obj, dict):
      return True
    elif isinstance(obj, Response):
      return True
    elif isinstance(obj, np.generic):
      return True
    return False

  def __call__(self, obj, base_encoder):
    if (isinstance(obj, float) and math.isnan(obj)):
      return None
    elif isinstance(obj, dict):
      df = pd.DataFrame.from_dict(obj, orient=index)
      json.dumps(df.where(pd.notnull(df), None))
    elif isinstance(obj, Response):
      return [NaNEncoder(item) for item in obj]
    elif isinstance(obj, np.generic):
      a = np.asscalar(obj)
      if (isinstance(a, float) and np.isnan(a)):
        return None
    else:
      return obj


encoder = NaNEncoder()


def create():
  return encoder
