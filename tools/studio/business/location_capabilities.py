"""Fixed location selectors; host injects its existing bounded location service.
No user-supplied paths, provider URLs, imports, or executable commands.
"""
import time
from model import StudioError
from .capability_adapters import descriptor,text,ident,num

def business_capabilities():
    selectors={'location':text(160),'scope':{'type':'enum','values':['approved','all']},'stop':ident(),'viewpoint':ident()}
    return [descriptor('location.query.v1','read',selectors,['location'],response=262144),
      descriptor('location.prepare.v1','mutation',dict(selectors,expectedRevision=num(0,9007199254740991),hydrate={'type':'boolean'},maxBytes=num(1,33554432),entityId=ident()),['location','expectedRevision','hydrate'],response=524288)]

def business_dispatch(store,operation,body,context):
    remaining=context['deadlineMonotonic']-time.monotonic()
    if remaining<=0:raise StudioError('Location deadline expired','business_timeout',504)
    if operation not in ('location.query.v1','location.prepare.v1'):raise StudioError('Unknown location operation','not_found',404)
    # Owner installs a trusted service with query/prepare methods in reloadable business.
    # Service must accept deadline and use bounded subprocess timeouts; cannot use
    # the legacy 195-second default prepare directly.
    service=getattr(store,'location_capability_service',None)
    if service is None:raise StudioError('Location capability host service is not configured','location_not_ready',503)
    selectors={k:body[k] for k in ('location','scope','stop','viewpoint') if k in body}
    if operation=='location.query.v1':
        if context['readOnly']:raise StudioError('Current location catalog is unavailable in historical view','read_only',403)
        return service.query(**selectors,deadline=context['deadlineMonotonic'],probe_media=False,network=False)
    if context['readOnly']:raise StudioError('Historical locations are read only','read_only',403)
    if body['expectedRevision']!=context['revision'] or store.read()['revision']!=context['revision']:raise StudioError('Workspace changed','revision_conflict',409)
    if body['hydrate']:raise StudioError('Cold hydration requires the existing asynchronous business job path; not configured by this adapter','location_hydration_pending',503)
    return service.prepare(store=store,**selectors,restore=False,max_bytes=body.get('maxBytes',33554432),entity_id=body.get('entityId'),deadline=context['deadlineMonotonic'])

class BoundedLocationService:
    """Trusted host configuration; paths are never supplied by capability requests."""
    def __init__(self,adapter,output_root,cache=None):
        self.adapter=adapter;self.output_root=output_root;self.cache=cache
    def _adapter(self,deadline):
        from .locations import LocationAdapter
        def runner(argv,**options):
            remaining=deadline-time.monotonic()-0.25
            if remaining<=0:raise StudioError('Location deadline expired','business_timeout',504)
            options['timeout']=min(options.get('timeout',remaining),remaining)
            return self.adapter.runner(argv,**options)
        return LocationAdapter(self.adapter.root,self.adapter.index,runner=runner,python=self.adapter.python)
    def query(self,location,deadline,probe_media=False,network=False,**selectors):
        if probe_media or network:raise StudioError('Location query is metadata only','business_contract',400)
        from .locations import LocationAdapterError
        try:return self._adapter(deadline).discover(location,**selectors)
        except LocationAdapterError as exc:raise StudioError(str(exc),'location_request',422)
    def prepare(self,store,location,deadline,restore=False,**selectors):
        from pathlib import Path
        import hashlib
        from .locations import LocationAdapterError
        # Safe deterministic scoped directory, never logical-ID path interpolation.
        output=Path(self.output_root)/hashlib.sha256(location.encode()).hexdigest()
        try:return self._adapter(deadline).prepare(store,location,output,self.cache,restore=restore,**selectors)
        except LocationAdapterError as exc:raise StudioError(str(exc),'location_request',422)
