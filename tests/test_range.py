from phovea_server.range import fix, RangeElem, SingleRangeElem, Range1D
from numpy import NaN, isnan
import pytest

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


class TestSingleRangeElem:
  VALUE = 5
  v = SingleRangeElem(VALUE)

  def test_attributes(self):
    v = self.v
    assert v.start == self.VALUE, 'from'
    assert v.end == self.VALUE + 1, 'to'
    assert v.step == 1, 'step'
    assert not v.isall, '!isAll'
    assert v.issingle, 'isSingle'
    assert not v.isunbound, '!isUnbound'
    assert str(v) == str(self.VALUE), 'toString'

  def test_size(self):
    v = self.v
    assert v.size() == 1, 'size'
    assert v.size(100) == 1, 'size(5)'

  def test_clone_and_reverse(self):
    v = self.v
    assert v.copy() == v, 'clone'
    assert v.reverse() == v, 'reverse'

  def test_iter(self):
    v = self.v
    assert list(v) == [self.VALUE], 'default'
    assert list(v.iter(100)) == [self.VALUE], 'dedicated size'

  def test_contains(self):
    v = self.v
    assert self.VALUE in v, 'contains value'
    assert (self.VALUE - 5) not in v, '!contains value'

  def test_invert(self):
    v = self.v
    assert v.invert(0) == self.VALUE, 'invert 0'
    assert v.invert(2) == 2 + self.VALUE, 'invert 2'


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

  def test_iter(self):
    assert list(RangeElem(0, 5)) == [0, 1, 2, 3, 4], 'default 0:5'
    assert list(RangeElem(4, -1, -1)) == [4, 3, 2, 1, 0], 'default 4:-1:-1'
    assert list(RangeElem(0, 5, 2)) == [0, 2, 4], 'default 0:5:2'
    assert list(RangeElem(0).iter(5)) == [0, 1, 2, 3, 4], 'default 0:-1 (5)'
    assert list(RangeElem(-2, -1, -1).iter(5)) == [4, 3, 2, 1, 0], 'default 0:-1 (5)'
    assert list(RangeElem(-1, 4, -1).iter(10)) == [10, 9, 8, 7, 6, 5], 'default -1:4:-1 (10)'

  def test_reverse(self):
    assert RangeElem(0).reverse() == RangeElem(-2, -1, -1), '0:-1'
    assert RangeElem(0, 5).reverse() == RangeElem(4, -1, -1), '0:5'
    assert RangeElem(2, 5).reverse() == RangeElem(4, 1, -1), '2:5'
    assert RangeElem(5, 2, -1).reverse() == RangeElem(1, 4), '5:2:-1'

  def test_invert(self):
    assert RangeElem(0).invert(5) == 5, '0:-1'
    assert RangeElem(0, 10).invert(5) == 5, '0:10'
    assert RangeElem(5, 20).invert(5) == 10, '5:20'
    assert RangeElem(20, -1, -1).invert(5) == 15, '20:-1:-1'

  def test_contains(self):
    assert RangeElem(0).contains(5), '0:-1 5'
    assert not RangeElem(0, 5).contains(10), '0:5 10'
    assert not RangeElem(0, 5).contains(5), '0:5 5'
    assert not RangeElem(0, 5).contains(-1), '0:5 -1'
    assert RangeElem(0, 10, 2).contains(2), '0:10:2 2'
    assert not RangeElem(0, 10, 2).contains(3), '0:10:2 3'
    assert RangeElem(10, -1, -1).contains(3), '10:-1:-1 3'
    assert RangeElem(10, -1, -2).contains(2), '10:-1:-2 2'

  def test_parse(self):
    assert RangeElem.parse('') == RangeElem.all(), '""'
    assert RangeElem.parse('::') == RangeElem.all(), '":"'
    assert RangeElem.parse('::') == RangeElem.all(), '"::"'
    assert RangeElem.parse('2') == RangeElem.single(2), '"2"'
    assert RangeElem.parse('2:5') == RangeElem(2, 5), '"2:5"'
    assert RangeElem.parse(':5') == RangeElem(0, 5), '":5"'
    assert RangeElem.parse('2:5:2') == RangeElem(2, 5, 2), '"2:5:2"'
    assert RangeElem.parse('::2') == RangeElem(0, -1, 2), '"::2"'
    with pytest.raises(Exception):
      RangeElem.parse('a')
    with pytest.raises(Exception):
      RangeElem.parse('0:a')


class TestRange1D:
  def test_all(self):
    elem = Range1D.all()
    assert elem.isall, 'isAll'
    assert elem.isunbound, 'isUnbound'
    assert elem.size(10) == 10, 'size'
    with pytest.raises(ValueError):
      assert isnan(len(elem)), 'length'

  def test_none(self):
    elem = Range1D.none()
    assert not elem.isall, '!isAll'
    assert not elem.isunbound, '!isUnbound'
    assert elem.size() == 0, 'size'
    assert len(elem) == 0, 'length'

  def test_single(self):
    elem = Range1D.single(5)
    assert not elem.isall, '!isAll'
    assert not elem.isunbound, '!isUnbound'
    assert elem.size() == 1, 'size'
    assert len(elem) == 1, 'length'

  def test_from(self):
    elem = Range1D.from_list([1, 2, 3])
    assert not elem.isall, '!isAll'
    assert not elem.isunbound, '!isUnbound'
    assert elem.size() == 3, 'size'
    assert len(elem) == 3, 'length'

  def test_compress(self):
    assert str(Range1D.from_list([1, 2, 3])) == '(1:4)', '1,2,3'
    assert str(Range1D.from_list([1, 2, 3, 6])) == '(1:4,6)', '1,2,3,6'
    # assert str(Range1D.from_list([1,2,3,9,8,7])) == '(1:4,9:6:-1)', '1,2,3,9,8,7'
    assert str(Range1D.from_list([1, 2, 3, 9, 8, 7])) == '(1:4,9,8,7)', '1,2,3,9,8,7'
