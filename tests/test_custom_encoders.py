from phovea_server.util import jsonify


class TestCustomEncoders:
  # def test_sets(self):
  #  assert jsonify(set()) == []

  def test_nan_values(self):
    test_var = float('nan')
    assert jsonify([test_var, 'This', 'is', 'a', 'very', 'complex', 'test', 'case', test_var]) == [None, "This", "is", "a", "very", "complex", "test", "case", None]
