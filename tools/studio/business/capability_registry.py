"""Additive trusted business registry; stable transport remains feature-independent."""
import os
from . import capability_adapters as draft
from . import book_capabilities as book
from . import location_capabilities as location
from . import compact_sheet as sheets
from . import location_media

def business_capabilities():
    return draft.business_capabilities()+book.business_capabilities()+location.business_capabilities()+sheets.business_capabilities()+location_media.business_capabilities()

def business_dispatch(store,operation,body,context):
    if operation.startswith('spaces.location.'):
        if not callable(getattr(location_media.archive,'media_entries',None)):
            from model import StudioError
            raise StudioError('Spaces media library requires the reviewed media artifact','location_not_ready',503)
        return location_media.business_dispatch(store,operation,body,context)
    if operation.startswith('draft.sheet.'):return sheets.business_dispatch(store,operation,body,context)
    if operation.startswith('book.'):return book.business_dispatch(store,operation,body,context)
    if operation.startswith('location.'):
        # Optional trusted host configuration, never supplied by request/project JSON.
        config=getattr(store,'location_capability_configuration',None)
        if config is None:
            names={'sourceRoot':'STUDIO_LOCATION_SOURCE_ROOT','indexPath':'STUDIO_LOCATION_INDEX_PATH','pythonPath':'STUDIO_LOCATION_PYTHON_PATH','outputRoot':'STUDIO_LOCATION_OUTPUT_ROOT','cacheRoot':'STUDIO_LOCATION_CACHE_ROOT'}
            config={key:os.environ[name] for key,name in names.items() if name in os.environ}
            if not config:config=None
        if isinstance(config,dict) and (getattr(store,'location_capability_service',None) is None or getattr(store,'_location_capability_business_hash',None)!=context['businessHash']):
            from model import StudioError
            required={'sourceRoot','indexPath','pythonPath','outputRoot'}
            if not required <= set(config) or set(config)-required-{'cacheRoot'} or any(not isinstance(config[k],str) or not config[k].startswith('/') for k in config):
                raise StudioError('Trusted location host configuration incomplete','location_not_ready',503)
            from .locations import LocationAdapter
            adapter=LocationAdapter(config['sourceRoot'],config['indexPath'],python=config['pythonPath'])
            store.location_capability_service=location.BoundedLocationService(adapter,config['outputRoot'],config.get('cacheRoot'))
            store._location_capability_business_hash=context['businessHash']
        return location.business_dispatch(store,operation,body,context)
    return draft.business_dispatch(store,operation,body,context)
