###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################


from . import plugin, range
import logging
from .dataset import list_idtypes, get_idmanager, iter, get_mappingmanager, get, list_datasets, add, remove

_log = logging.getLogger(__name__)


def get_map(idtype, idnames):
  return jsonify(get_idmanager()(idnames, idtype))


def get_map_single(idtype, idname):
  return get_idmanager()([idname], idtype)[0]


def get_unmap(idtype, ids):
  names = ids.tolist()
  return jsonify(get_idmanager().unmap(names, idtype))


def get_unmap_single(idtype, id):
  return get_idmanager().unmap([id], idtype)[0]


def get_maps_to(idtype):
  mapper = get_mappingmanager()
  target_id_types = mapper.maps_to(idtype)
  return target_id_types


def get_convert(source, target, uids, q, mode):
  return _do_mapping(source, target, uids, q, mode, False)


def get_convert_id(source, target, uids, q, mode):
  return _do_mapping(source, target, uids, q, mode, True)


def get_convert_single(source, target, uid, mode):
  return _do_mapping_single(source, target, uid, mode, False)


def get_convert_single_id(source, target, uid, mode):
  return _do_mapping_single(source, target, uid, mode, True)


def _do_mapping(source, target, uids, q, mode, to_ids):
  first_only = mode == 'first'

  if uids:
    uids = uids[0].tolist()
  elif q:
    uids = q
  names = get_idmanager().unmap(uids, source)
  mapped_list = _perform_mapping(source, target, names, first_only, to_ids)
  return mapped_list


def _do_mapping_single(source, target, uid, mode, to_ids):
  first_only = mode == 'first'

  names = get_idmanager().unmap([uid], source)
  mapped_list = _perform_mapping(source, target, names, first_only, to_ids)

  return mapped_list[0] if first_only else mapped_list[0]


def _perform_mapping(source, target, names, first_only, to_ids):
  mapper = get_mappingmanager()
  mapped_list = mapper(source, target, names)
  if first_only:
    mapped_list = [None if a is None or len(a) == 0 else a[0] for a in mapped_list]

  if to_ids:
    m = get_idmanager()
    if first_only:
      mapped_list = m(mapped_list, target)
    else:
      mapped_list = [m(entry, target) for entry in mapped_list]
  return mapped_list
