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
        from .location_host import ensure_location_service
        ensure_location_service(store,context['businessHash'])
        return location.business_dispatch(store,operation,body,context)
    return draft.business_dispatch(store,operation,body,context)
