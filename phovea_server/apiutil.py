from phovea_server.ns import Namespace
from ns.ext.restplus import Api, apidoc

def create_api(name, **kwargs):
  """
  utility function for creating an flask restplus api having the docu accessable under /doc and not the root
  """
  app = Namespace(name)
  app.debug = True
  api = Api(app, ui=False, **kwargs)

  #remove the stupid root rule
  try:
    for rule in app.url_map.iter_rules('root'):
      app.url_map._rules.remove(rule)
  except ValueError:
    # no static view was created yet
    pass
  #create a doc rule
  @app.route('/doc/', endpoint='doc')
  def swagger_ui():
      return apidoc.ui_for(api)
  app.register_blueprint(apidoc.apidoc)  # only needed for assets and templates

  return app, api
