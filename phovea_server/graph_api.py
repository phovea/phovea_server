__author__ = 'Samuel Gratzl'

from caleydo_server.util import jsonify
import flask
import caleydo_server.websocket as ws


def asrange(r = None):
  if r is None:
    return None
  import caleydo_server.range as ranges
  return ranges.parse(r)

def _to_desc():
  if 'desc' in flask.request.values:
    import json
    n = json.loads(flask.request.values['desc'])
  else:
    n = flask.request.values
  return n


def format_json(dataset, range, args):
  d = dataset.asjson(range)
  if bool(args.get('f_pretty_print', False)):
    return jsonify(d, indent=' ')
  return jsonify(d)

def resolve_formatter(type, format):
  import caleydo_server.plugin
  for p in caleydo_server.plugin.list(type+'-formatter'):
    if p.format == format:
      return p.load()
  flask.abort(400,'unknown format "{0}" possible formats are: {1}'.format(format, ','.join((p.format for p in caleydo_server.plugin.list(type+'-formatter')))))

def _list_type(dataset_getter, name = 'node'):
  def list_items(datasetid):
    d = dataset_getter(datasetid, 'graph')
    if flask.request.method == 'GET':
      r = asrange(flask.request.args.get('range',None))
      return jsonify([n.asjson() for n in getattr(d,name+'s')(r[0] if r is not None else None)])

    if flask.request.method == 'DELETE':
      if d.clear():
        return jsonify(d.to_description(),indent=1)
      flask.abort(400)

    #post
    n = _to_desc()
    if getattr(d,'add_'+name)(n):
      return jsonify(d.to_description(),indent=1)
    #invalid upload
    flask.abort(400)

  def handle_item(datasetid, itemid):
    d = dataset_getter(datasetid, 'graph')
    if flask.request.method == 'GET':
      n = getattr(d,'get_'+name)(itemid)
      return jsonify(n.asjson())

    if flask.request.method == 'DELETE':
      if getattr(d,'remove_'+name)(itemid):
        return jsonify(d.to_description(),indent=1)
      flask.abort(400)

    #put
    n = _to_desc()
    n['id'] = itemid
    if getattr(d,'update_'+name)(n):
      return jsonify(d.to_description(),indent=1)
    #invalid upload
    flask.abort(400)

  return list_items, handle_item

def add_graph_handler(app, dataset_getter):
  @app.route('/graph/<datasetid>')
  def list_graphs(datasetid):
    d = dataset_getter(datasetid, 'graph')
    return jsonify(d.to_description())

  @app.route('/graph/<datasetid>/data')
  def get_graph_data(datasetid):
    d = dataset_getter(datasetid, 'graph')
    r = asrange(flask.request.args.get('range',None))
    formatter = resolve_formatter('graph', flask.request.args.get('format','json'))
    return formatter(d, r, args=flask.request.args)

  list_nodes, handle_node = _list_type(dataset_getter, 'node')
  app.add_url_rule('/graph/<datasetid>/node','list_nodes', list_nodes, methods=['GET','POST','DELETE'])
  app.add_url_rule('/graph/<datasetid>/node/<int:itemid>','handle_node', handle_node, methods=['GET','PUT', 'DELETE'])

  list_edges, handle_edge = _list_type(dataset_getter, 'edge')
  app.add_url_rule('/graph/<datasetid>/edge','list_edges', list_edges, methods=['GET','POST','DELETE'])
  app.add_url_rule('/graph/<datasetid>/edge/<int:itemid>','handle_edge', handle_edge, methods=['GET','PUT', 'DELETE'])

  #websocket = ws.Socket(app)
  #@websocket.route('/ws')
  #def graph_ws(socket):
  #  ws.websocket_loop(socket, dict(get_graph=(payload, s)))
