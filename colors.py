
__author__ = 'Samuel Gratzl'

def _mix(a,b,alpha):
  if isinstance(a, tuple):
    return tuple([_mix(ai, bi, alpha) for ai,bi in zip(a,b)])
  return int(a*(1-alpha) + b*alpha)

class ColorPalette(object):
  def __init__(self, *colors):
    self._colors = colors

  def as_palette(self):
    l = len(self._colors)
    if l == 1:
      return self._colors * 256 #repeat the same color for the full range
    elif l == 2:
      a = self._colors[0]
      b = self._colors[1]
      return [ _mix(a,b,i/256.) for i in xrange(256)]
    elif l == 3:
      a = self._colors[0]
      center = self._colors[1]
      b = self._colors[2]
      center_a = _mix(a,center,127.5/128)
      center_b = _mix(center,b,0.5/128)
      return [ _mix(a,center_a,i/128.) for i in xrange(128)] + [ _mix(center_b,b,i/128.) for i in xrange(128)]
    return None #not yet done

neutral_grey=(220,220,220)
blue_white_red=ColorPalette((5,113,176),neutral_grey,(202,0,32))
white_red=ColorPalette(neutral_grey,(202,0,32))
