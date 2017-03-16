from phovea_server.range import fix
from numpy import NaN, isnan

__author__ = 'Samuel Gratzl'


class TestFix:
  def test_constant(self):
    assert fix(1, 10) == 1

  def test_constant_negative_size(self):
    assert fix(10, -1) == 10

  def test_constant_negative_size2(self):
    assert fix(10, NaN) == 10

  def test_fix_m1(self):
    assert fix(-1, 10) == 10

  def test_fix_m2(self):
    assert fix(-2, 10) == 9

  def test_fix_m1_nan(self):
    assert isnan(fix(-1, NaN))

  def test_fix_m8(self):
    assert fix(-8, 10) == 3

  def test_fix_m13(self):
    assert fix(-13, 10) == -2
