from phovea_server import server


def test_application():
  assert server.application is not None
