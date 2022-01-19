###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from ..ns import Namespace, etag, request
from ..range import parse
from ..util import jsonify
import logging
from ..dataset import list_idtypes, get_idmanager
from . import get_mappingmanager
from flask import abort

app_idtype = Namespace(__name__)
_log = logging.getLogger(__name__)


@app_idtype.route('/')
@etag
def _list_idtypes():
    return jsonify(list_idtypes())


@app_idtype.route('/<idtype>/map', methods=['GET', 'POST'])
def _map_ids(idtype):
    name = request.values.get('id', None)
    if name is not None:
        return get_idmanager()([name], idtype)[0]
    names = request.values.getlist('ids[]')
    return jsonify(get_idmanager()(names, idtype))


@app_idtype.route('/<idtype>/unmap', methods=['GET', 'POST'])
def _unmap_ids(idtype):
    name = request.values.get('id', None)
    if name is not None:
        return get_idmanager().unmap([int(name)], idtype)[0]
    names = parse(request.values.get('ids', ''))[0].tolist()
    return jsonify(get_idmanager().unmap(names, idtype))


@app_idtype.route('/<idtype>/')
@etag
def _maps_to(idtype):
    mapper = get_mappingmanager()
    target_id_types = mapper.maps_to(idtype)
    return jsonify(target_id_types)


@app_idtype.route('/<idtype>/search')
def _search_ids(idtype):
    query = request.args.get('q', None)
    max_results = int(request.args.get('limit', 10))
    manager = get_idmanager()
    if query is None:
        return abort(400, 'Parameter "q" must be defined')
    if hasattr(manager, 'search'):
        return jsonify(manager.search(idtype, query, max_results))
    return jsonify([])


@app_idtype.route('/<idtype>/<to_idtype>', methods=['GET', 'POST'])
def _mapping_to(idtype, to_idtype):
    return _do_mapping(idtype, to_idtype, False)


@app_idtype.route('/<idtype>/<to_idtype>/search')
def _mapping_to_search(idtype, to_idtype):
    query = request.args.get('q', None)
    max_results = int(request.args.get('limit', 10))
    mapper = get_mappingmanager()
    if hasattr(mapper, 'search'):
        return jsonify(mapper.search(idtype, to_idtype, query, max_results))
    return jsonify([])


def _do_mapping(idtype, to_idtype, to_ids):
    mapper = get_mappingmanager()
    args = request.values
    first_only = args.get('mode', 'all') == 'first'

    if 'id' in args:
        names = get_idmanager().unmap([int(args['id'])], idtype)
    elif 'ids' in args:
        names = get_idmanager().unmap(parse(args['ids'])[0].tolist(), idtype)
    elif 'q' in args:
        names = args['q'].split(',')
    elif 'q[]' in args:
        names = args.getlist('q[]')
    else:
        abort(400)
        return

    mapped_list = mapper(idtype, to_idtype, names)

    if first_only:
        mapped_list = [None if a is None or len(a) == 0 else a[0] for a in mapped_list]

    if to_ids:
        m = get_idmanager()
        if first_only:
            mapped_list = m(mapped_list, to_idtype)
        else:
            mapped_list = [m(entry, to_idtype) for entry in mapped_list]

    return jsonify(mapped_list)


@app_idtype.route('/<idtype>/<to_idtype>/map', methods=['GET', 'POST'])
def _mapping_to_id(idtype, to_idtype):
    return _do_mapping(idtype, to_idtype, True)


def create():
    return app_idtype
