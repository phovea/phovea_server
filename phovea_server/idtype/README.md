# ID Mapping
This package TODO

## Packages

mapper.py
mapping_<>.py
api.py
### How to use the mapping manager

```python
from phovea_server.idtype import get_mappingmanager()

mapping_manager = get_mappingmanager()

mapping_manager.add_mapping([
    ('from', 'to', lambda ids: ids)
])
```

### How to create your own mapping provider
TODO

## API
TODO: Create flask-smorest or other self-documenting API endpoint (/api/idtype/spec)

* Explain usage via __init__.py registry things
* Explain role of mapping_provider and mapping_manager (graph)
* Explain API routes
  * Add example to convert from GeneSymbol to EntrezGene via endpoint
  * /api/idtype/GeneSymbol/EntrezGene?q=EGFR  
  * /api/idtype/GeneSymbol/EntrezGene?id=123 <-- internal redis ID
* Transitivity
