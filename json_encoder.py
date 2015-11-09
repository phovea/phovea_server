__author__ = 'Samuel Gratzl'

import numpy as np
import numpy.ma as ma

class NumpyTablesEncoder(object):
  def __contains__(self, obj):
    if isinstance(obj, np.ndarray):
      return True
    if isinstance(obj, np.generic):
      return True
    return False

  def __call__(self, obj, base_encoder):
    if isinstance(obj, np.ndarray):
      if obj.ndim == 1:
        return [base_encoder.default(x) for x in obj]
      else:
        return [base_encoder.default(obj[i]) for i in range(obj.shape[0])]
    if isinstance(obj, np.generic):
      a = np.asscalar(obj)
      if (isinstance(a, float) and np.isnan(a)) or ma.is_masked(a):
        return None
      return a
    return None

n = NumpyTablesEncoder()

def create():
  return n
