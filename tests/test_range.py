from phovea_server.range import fix, RangeElem
from numpy import NaN, isnan

__author__ = 'Samuel Gratzl'


class TestFix:
  def test_constant(self):
    assert fix(1, 10) == 1
    assert fix(0, 10) == 0

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


class TestRangeElem:
  def test_start(self):
    assert RangeElem(0).start == 0, 'default'
    assert RangeElem(2).start == 2, 'set value'

  def test_end(self):
    assert RangeElem(0).end == -1, 'default'
    assert RangeElem(0, 2).end == 2, 'set value'

  def test_step(self):
    assert RangeElem(0).step == 1, 'default'
    assert RangeElem(0, 2, 1).step == 1, 'set value'
    assert RangeElem(0, 2, 2).step == 2, 'set value'

  def test_isall(self):
    assert RangeElem(0).isall, 'default'
    assert RangeElem(0, -1).isall, 'explicit'
    assert RangeElem(0, -1, 1).isall, 'explicit full'
    assert not RangeElem(1).isall, 'not'
    assert not RangeElem(0, 5).isall, 'not explicit'
    assert not RangeElem(0, -1, 2).isall, 'not explicit full'

  def test_issingle(self):
    assert not RangeElem(0).issingle, 'default'
    assert not RangeElem(0, -1).issingle, 'all'
    assert RangeElem(0, 1).issingle, 'single 0:1'
    assert RangeElem(1, 2).issingle, 'single 1:2'
    assert RangeElem(4, 6, 2).issingle, 'single 4:6:2'
    assert RangeElem(6, 5, -1).issingle, 'single 6:5:-1'

  def test_isunbound(self):
    assert RangeElem(0).isunbound, 'default'
    assert RangeElem(0, -1).isunbound, 'explicit'
    assert not RangeElem(0, 2).isunbound, 'bound'
    assert RangeElem(-2, 2).isunbound, 'unbound negative start'

  def test_all(self):
    elem = RangeElem.all()
    assert elem.isall, 'isAll'
    assert not elem.issingle
    assert elem.isunbound, 'isUnbound'
    assert elem.start == 0, 'start'
    assert elem.end == -1, 'end'
    assert elem.step == 1, 'step'
    assert elem.size(10) == 10, 'size'

  def test_none(self):
    elem = RangeElem.none()
    assert not elem.isall, '!isAll'
    assert not elem.issingle, '!isSingle'
    assert not elem.isunbound, '!isUnbound'
    assert elem.start == 0, 'start'
    assert elem.end == 0, 'end'
    assert elem.step == 1, 'step'
    assert elem.size() == 0, 'size'

  def test_single(self):
    elem = RangeElem.single(5)
    assert not elem.isall, '!isAll'
    assert elem.issingle, 'isSingle'
    assert not elem.isunbound, '!isUnbound'
    assert elem.start == 5, 'start'
    assert elem.end == 6, 'end'
    assert elem.step == 1, 'step'
    assert elem.size() == 1, 'size'

  def test_size(self):
    assert RangeElem(0, 5).size() == 5, 'default 0:5'
    assert RangeElem(4, -1, -1).size() == 5, 'default 4:-1:-1'
    assert RangeElem(0, 5, 2).size() == 3, 'default 0:5:2'
    assert RangeElem(0).size(5) == 5, 'default 0:-1 (5)'
    assert RangeElem(-1, 4, -1).size(10) == 6, 'default -1:4:-1 (10)'
