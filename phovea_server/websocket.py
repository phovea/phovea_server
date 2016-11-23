###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from builtins import object
from flask_sockets import Sockets as Socket  # noqa 
from geventwebsocket import WebSocketError  # noqa 
import logging

_log = logging.getLogger(__name__)


class WebsocketSend(object):
  def __init__(self, ws):
    self._ws = ws

  def send(self, msg_type, payload):
    import pandas.json as ujson
    d = ujson.dumps(dict(type=msg_type, data=payload))
    self._ws.send(d)

  def send_str(self, msg_type, payload_as_string):
    d = '{{ "type": "{}", "data": {}}}'.format(msg_type, payload_as_string)
    self._ws.send(d)


def websocket_loop(ws, handler_map):
  import pandas.json as ujson
  while True:
    msg = ws.receive()
    if msg is None:
      continue
    _log.debug('msg received %s', msg)
    data = ujson.loads(msg)
    t = data['type']
    payload = data['data']

    if t not in handler_map:
      _log.warning('no handler defined for message of type: %s', t)
    else:
      handler_map[t](payload, WebsocketSend(ws))
