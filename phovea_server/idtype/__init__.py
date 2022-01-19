from ..plugin import lookup
from .mapper import MappingManager


def get_mappingmanager() -> MappingManager:
    return lookup('mappingmanager')
