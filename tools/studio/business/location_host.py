"""Trusted host-only location service construction shared by native and named routes."""
import os
from . import location_capabilities as location

def ensure_location_service(store,business_hash=None):
    # Optional trusted host configuration, never supplied by request/project JSON.
    config=getattr(store,'location_capability_configuration',None)
    if config is None:
        names={'sourceRoot':'STUDIO_LOCATION_SOURCE_ROOT','indexPath':'STUDIO_LOCATION_INDEX_PATH','pythonPath':'STUDIO_LOCATION_PYTHON_PATH','outputRoot':'STUDIO_LOCATION_OUTPUT_ROOT','cacheRoot':'STUDIO_LOCATION_CACHE_ROOT'}
        config={key:os.environ[name] for key,name in names.items() if name in os.environ}
        if not config:config=None
    if isinstance(config,dict) and (getattr(store,'location_capability_service',None) is None or getattr(store,'_location_capability_business_hash',None)!=business_hash):
        from model import StudioError
        required={'sourceRoot','indexPath','pythonPath','outputRoot'}
        if not required <= set(config) or set(config)-required-{'cacheRoot'} or any(not isinstance(config[k],str) or not config[k].startswith('/') for k in config):
            raise StudioError('Trusted location host configuration incomplete','location_not_ready',503)
        from .locations import LocationAdapter
        adapter=LocationAdapter(config['sourceRoot'],config['indexPath'],python=config['pythonPath'])
        store.location_capability_service=location.BoundedLocationService(adapter,config['outputRoot'],config.get('cacheRoot'))
        store._location_capability_business_hash=business_hash
    return getattr(store,'location_capability_service',None)
