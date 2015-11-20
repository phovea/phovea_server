__author__ = 'Samuel Gratzl'

from flask_sockets import Sockets as Socket
from geventwebsocket import WebSocketError

class WebsocketSend(object):
  def __init__(self, ws):
    self._ws = ws

  def send(self, msg_type, payload):
    import json
    d = json.dumps(dict(type=msg_type,data=payload))
    self._ws.send(d)

  def send_str(self, msg_type, payload_as_string):
    d = '{ "type": "'+msg_type+'", "data": '+str(payload_as_string)+'}'
    self._ws.send(d)

def websocket_loop(ws, handler_map):
  import json
  while True:
    msg = ws.receive()
    if msg is None:
      continue
    print msg
    data = json.loads(msg)
    t = data['type']
    payload = data['data']


    if t not in handler_map:
      print 'no handler defined for message of type: '+t
    handler_map[t](payload, WebsocketSend(ws))
