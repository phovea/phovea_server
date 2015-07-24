__author__ = 'Samuel Gratzl'

def socket_client(app):
  from flask_sockets import Sockets
  return Sockets(app)
