from phovea_server.util import to_json


class TestCustomEncoders:
  # def test_sets(self):
  #  assert jsonify(set()) == []

  def test_nan_values(self):
    test_var = float('nan')
    test_result = to_json(dict(myNum=test_var))
    assert test_result == {"myNum": None}
