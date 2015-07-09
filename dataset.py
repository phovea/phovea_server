import flask
import plugin
import range
import util

app = flask.Flask(__name__)
app_idtype = flask.Flask(__name__)

#create the api application

_providers_r = None
def _providers():
  global _providers_r
  if _providers_r is None:
    _providers_r = [p.load().factory() for p in plugin.list('dataset-provider')]
  return _providers_r

_dataset_r = None
def _datasets():
  global _dataset_r
  if _dataset_r is None: #lazy load the datasets
    r = []
    #check all dataset provider plugins
    for p in _providers():
      r.extend(p)
    _dataset_r = r
  return _dataset_r

def __iter__():
  return iter(_datasets())

def list_datasets():
  return _datasets()

def _list_format_json(data):
  return util.jsonify(data)

def _list_format_treejson(data):
  r = dict()
  for d in data:
    levels = d['fqname'].split('/')
    act = r
    for level in levels[:-1]:
      if level not in act:
        act[level] = dict()
      act = act[level]
    act[d['name']] = d
  return util.jsonify(r, indent=1)

def _list_format_csv(data):
  delimiter = flask.request.args.get('f_delimiter',';')
  def gen():
    yield delimiter.join(['ID','Name','FQName','Type','Size','Entry'])
    for d in data:
      yield '\n'
      yield delimiter.join([str(d['id']), d['name'], d['fqname'], d['type'], ','.join(str(d) for d in d['size']), util.to_json(d)])
  return flask.Response(gen(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=dataset.csv'})

@app.route('/')
def _list_datasets():
  ds = list_datasets()
  def with_id(d, i):
    d['id'] = i
    return d
  data = [with_id(d.to_description(),i) for i,d in enumerate(ds)]
  format = flask.request.args.get('format','json')
  formats = dict(json=_list_format_json,treejson=_list_format_treejson,csv=_list_format_csv)
  if format not in formats:
    flask.abort(flask.make_response('invalid format: "{0}" possible ones: {1}'.format(format,','.join(formats.keys())), 400))
  return formats[format](data)

def get(dataset_id):
  return  _datasets()[dataset_id]

@app.route('/<int:dataset_id>')
def _get_dataset(dataset_id):
  d = get(dataset_id)
  r = flask.request.args.get('range', None)
  if r is not None:
    r = range.parse(r)
  return util.jsonify(d.asjson(r))

def _dataset_getter(dataset_id, dataset_type):
  if dataset_id < 0:
    return [d for d in _datasets() if d.type == dataset_type]
  t = get(dataset_id)
  if t is None:
    flask.abort(404) #,extra='invalid dataset id "'+str(dataset_id)+'"')
  if t.type != dataset_type:
    flask.abort(400) #,extra='the given dataset "'+str(dataset_id)+'" is not a '+dataset_type)
  return t

#add all specific handler
for handler in plugin.list('dataset-specific-handler'):
  p = handler.load()
  p(app, _dataset_getter)


def create_dataset():
  return app

def list_idtypes():
  tmp = dict()
  for d in _datasets():
    for idtype in d.to_idtype_descriptions():
      tmp[idtype['id']] = idtype
  return tmp.values()

@app_idtype.route('/')
def _list_idtypes():
  return util.jsonify(list_idtypes())


def create_idtype():
  return app_idtype

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=9000)
