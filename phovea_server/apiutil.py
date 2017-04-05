###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from flask import Flask
from flask_restplus import Api, apidoc, Resource  # noqa


def create_api(name, **kwargs):
  """
  utility function for creating an flask restplus api having the docu accessable under /doc and not the root
  """
  app = Flask(name)
  app.debug = True
  api = Api(app, ui=False, **kwargs)

  return app, api
