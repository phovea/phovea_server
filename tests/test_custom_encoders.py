from phovea_server.util import JSONExtensibleEncoder, to_json
import json


class TestCustomEncoders:
  def test_sets(self):
    test_set = set()
    test_resultset = json.dumps(test_set, cls=JSONExtensibleEncoder)
    assert test_resultset == '[]'

  def test_nan_values(self):
    test_var = float('nan')
    test_result = to_json(dict(myNum=test_var))
    assert test_result == '{"myNum": null}'
