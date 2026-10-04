
import argparse, ast, copy, json, sys, types, unittest
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--studio-dir', required=True)
args, remaining=parser.parse_known_args()
sys.path.insert(0,args.studio_dir)
from model import StudioError, find, valid_id
module=types.ModuleType('draft_under_test')
exec(compile(CANDIDATE if 'CANDIDATE' in globals() else (Path(args.studio_dir)/'business/chapter_drafts.py').read_text(), 'chapter_drafts.py','exec'),module.__dict__)
tree=ast.parse(ROUTES if 'ROUTES' in globals() else (Path(args.studio_dir)/'business/routes.py').read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='route')
ns=dict(module.__dict__,find=find,valid_id=valid_id,state_at_revision=lambda store,revision:dict(store.read(),readOnly=revision is not None))
exec(compile(ast.Module(body=[function],type_ignores=[]),'routes.py','exec'),ns)
route=ns['route']
class MemoryStore:
    """Revision-checked JSON round-trip double; real disk Store tests are separate."""
    def __init__(self):
        self.state={'revision':0,'assets':[],'jobs':[],'project':{'chapters':[],
            'entities':[{'id':'hero','kind':'character'},{'id':'forest','kind':'location'}]}}
    def read(self): return copy.deepcopy(self.state)
    def save_project(self,project,revision):
        if revision!=self.state['revision']: raise StudioError('Revision changed')
        self.state=json.loads(json.dumps(dict(self.state,project=project,revision=revision+1)))
        return self.read()
class GoContract(unittest.TestCase):
    def setUp(self):
        self.store=MemoryStore()
        spec={'title':'Fixture','synopsis':'A leaf settles','referenceIds':[],
            'location':{'baseEntityId':'forest','description':'Proposed clearing','proposed':True},
            'panels':[{'id':'one','action':'Watch leaf','cause':'Wind stops','effect':'Leaf settles',
                'caption':'Hmm','camera':'Close-up','seconds':5,'beat':'turn','castIds':['hero'],
                'dependsOn':[],'previewKind':'schematic-placeholder'}]}
        route(self.store,'POST','/api/chapter-drafts',{},dict(chapterId='fixture',baseVersion=0,expectedRevision=0,spec=spec))
    def chapter(self): return self.store.read()['project']['chapters'][0]
    def go(self):
        _,result=route(self.store,'GET','/api/chapter-drafts',{'chapterId':['fixture']},None)
        d=result['draft']
        return dict(chapterId='fixture',version=d['currentVersion'],sha256=d['sha256'],
            referenceHash=d['referenceHash'],expectedRevision=result['revision'],
            explicitFullProductionGo=True,userInstruction='Explicit fixture go for full production.')
    def dispatch(self,scope='full-production'):
        module.dispatch_preflight(self.store,self.store.read(),self.chapter(),dict(kind='illustration',productionScope=scope,sceneIds=[]))
    def test_receipt_route_and_no_dispatch(self):
        _,r=route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go())
        self.assertEqual(self.chapter()['studioDraft']['productionAuthorization'],r['receipt'])
        self.assertEqual(self.store.read()['jobs'],[])
        self.dispatch()
    def test_stale_and_historical(self):
        for fields in ({'version':0},{'sha256':'0'*64},{'referenceHash':'0'*64},
                       {'revision':1},{'readOnly':True},{'reviewSnapshot':True},{'expectedRevision':0}):
            before=self.store.read()
            with self.assertRaises(StudioError): route(self.store,'POST','/api/chapter-drafts/authorize-production',{},dict(self.go(),**fields))
            self.assertEqual(before,self.store.read())
    def test_edit_requires_fresh_go_and_preserves_receipt(self):
        _,r=route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go())
        v=module.current(self.chapter())
        route(self.store,'POST','/api/chapter-drafts/patch',{},dict(chapterId='fixture',baseVersion=v['version'],baseSHA256=v['sha256'],
            expectedRevision=self.store.read()['revision'],patches=[dict(panelId='one',fields={'caption':'Settled'})]))
        self.assertNotIn('productionAuthorization',self.chapter()['studioDraft'])
        self.assertEqual(self.chapter()['studioDraft']['authorizationReceipts'],[r['receipt']])
        with self.assertRaises(StudioError): self.dispatch()
        route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go());self.dispatch()
    def test_legacy_and_rough(self):
        self.dispatch('rough-preproduction')
        with self.assertRaises(StudioError): self.dispatch()
        v=module.current(self.store.state['project']['chapters'][0])
        v.pop('referenceHash');v.pop('referenceBindings');frozen=copy.deepcopy(v)
        route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go())
        self.assertEqual(module.current(self.chapter()),frozen);self.dispatch()
    def test_catalog_role_change(self):
        a={'id':'ref','sha256':'a'*64,'bytes':1,'provenance':{'role':'style'}}
        self.store.state['assets']=[a]
        v=module.current(self.store.state['project']['chapters'][0]);v['spec']['referenceIds']=['ref']
        # Catalog-only fixture deliberately unresolved during review.
        self.store.asset_path=lambda *args:Path('/nonexistent-fixture-reference')
        v['referenceHash']=module.binding_hash(module.references(self.store,self.store.read(),v['spec']))
        body=self.go()
        self.store.state['assets'][0]['provenance']['role']='identity'
        with self.assertRaises(StudioError):route(self.store,'POST','/api/chapter-drafts/authorize-production',{},body)
    def test_historical_query_rejected(self):
        with self.assertRaises(StudioError):
            route(self.store,'POST','/api/chapter-drafts/authorize-production',{'revision':['1']},self.go())
    def test_spec_mutation_invalidates_receipt(self):
        route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go())
        module.current(self.store.state['project']['chapters'][0])['spec']['panels'][0]['seconds']=6
        with self.assertRaises(StudioError):self.dispatch()
    def test_empty_selection_checks_scene_staging(self):
        route(self.store,'POST','/api/chapter-drafts/authorize-production',{},self.go())
        self.store.state['project']['chapters'][0]['scenes'][0]['action']='Drifted'
        with self.assertRaises(StudioError):self.dispatch()
if __name__=='__main__':
    unittest.main(argv=[sys.argv[0],*remaining])
