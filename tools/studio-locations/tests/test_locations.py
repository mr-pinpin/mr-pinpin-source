"""Portable contract tests; fixtures never invoke network or paid generation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
MODULES=HERE if (HERE/'cli.py').exists() else HERE/'tools/studio-locations'
sys.path.insert(0,str(MODULES))
from paths import LocationError, external_path, metadata_path, media_path
from indexer import build, read_index
from query import query
from hydration import hydrate


def write_json(root,name,value):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return p


class LocationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name).resolve();self.root=self.base/'source';self.root.mkdir()
        self.index=self.base/'index.json'
        self.book=b'approved fixture book';self.draft=b'candidate fixture panorama'
        assets=[]
        for name,raw in [('docs/book.png',self.book),('docs/draft.png',self.draft)]:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            sha=hashlib.sha256(raw).hexdigest()
            assets.append({'path':name,'role':'archive','bytes':len(raw),'sha256':sha,'object':'sha256/'+sha[:2]+'/'+sha+'/'+p.name})
        write_json(self.root,'assets/test.json',{'version':1,'bucket':'miguelemosreverte/mr-pinpin-archive','assets':assets})
        write_json(self.root,'docs/references.json',{'references':[{'id':'book','path':'docs/book.png','sha256':assets[0]['sha256'],'bytes':len(self.book),'roles':['style'],'notes':'Actual approved fixture book'}]})
        write_json(self.root,'docs/generation.json',{'output':{'path':'docs/draft.png','sha256':assets[1]['sha256'],'bytes':len(self.draft)},'status':'candidate'})
        write_json(self.root,'workflows/locations/catalog.json',{'schemaVersion':1,'scanRoots':['docs/'],'catalogGlobs':['assets/*.json'],'allowedMetadataExtensions':['.json','.md','.txt','.js'],'entries':[{'id':'house/bath','aliases':['bathroom'],'kind':'measured-geometry','approval':'geometry-study','approvalEvidence':'docs/generation.json','room':'bath','referenceIds':['book'],'documents':['docs/*.json'],'recipes':[],'connections':[],'limitations':['not measured uniform orbit']}]})
        adapter=self.root/'tools/assets/hf_store.py';adapter.parent.mkdir(parents=True);adapter.write_text('# fixture adapter must never run\n')
        build(self.root,self.index);self.catalog=read_index(self.root,self.index)

    def tearDown(self):self.temp.cleanup()

    def test_index_enumeration_never_stats_binary(self):
        original=Path.stat
        def checked(path,*args,**kwargs):
            if path.suffix in {'.png','.webp','.mp4'}:raise AssertionError('binary stat forbidden')
            return original(path,*args,**kwargs)
        with patch.object(Path,'stat',checked):build(self.root,self.index)

    def test_cold_job_timeout_preserves_last_queryable_cache(self):
        before=self.index.read_bytes()
        result=subprocess.run([sys.executable,'-B',str(MODULES/'index_job.py'),'--root',str(self.root),'--index',str(self.index),'--diagnostics',str(self.base/'diagnostics'),'--timeout-seconds','0.001'],capture_output=True,text=True,timeout=5)
        proof=json.loads(result.stdout)
        self.assertEqual(result.returncode,3);self.assertEqual(proof['status'],'timeout')
        self.assertTrue(proof['oldIndexPreserved']);self.assertFalse(proof['published'])
        self.assertEqual(self.index.read_bytes(),before)
        self.assertEqual(query(read_index(self.root,self.index),self.root,'bathroom')['request']['location'],'house/bath')
        self.assertTrue(Path(proof['resultPath']).exists())

    def test_cold_job_failed_scan_preserves_old_cache(self):
        before=self.index.read_bytes();(self.root/'docs/generation.json').write_text('{malformed')
        result=subprocess.run([sys.executable,'-B',str(MODULES/'index_job.py'),'--root',str(self.root),'--index',str(self.index),'--diagnostics',str(self.base/'diagnostics'),'--timeout-seconds','5'],capture_output=True,text=True,timeout=10)
        proof=json.loads(result.stdout)
        self.assertEqual(result.returncode,3);self.assertFalse(proof['published'])
        self.assertTrue(proof['oldIndexPreserved']);self.assertEqual(self.index.read_bytes(),before)

    def test_cold_job_publishes_only_complete_candidate(self):
        result=subprocess.run([sys.executable,'-B',str(MODULES/'index_job.py'),'--root',str(self.root),'--index',str(self.index),'--diagnostics',str(self.base/'diagnostics'),'--timeout-seconds','5'],capture_output=True,text=True,timeout=10)
        proof=json.loads(result.stdout)
        self.assertEqual(result.returncode,0);self.assertEqual(proof['status'],'complete')
        self.assertTrue(proof['published']);self.assertFalse(Path(proof['candidatePath']).exists())
        self.assertEqual(read_index(self.root,self.index)['schemaVersion'],1)
        self.assertTrue(Path(proof['progressPath']).exists())

    def test_valid_alias(self):
        value=query(self.catalog,self.root,'bathroom');self.assertEqual(value['request']['location'],'house/bath')
        self.assertEqual([m['path'] for m in value['media']],['docs/book.png'])

    def test_unknown(self):
        with self.assertRaises(LocationError):query(self.catalog,self.root,'invented room')

    def test_draft_not_approved(self):
        value=query(self.catalog,self.root,'bathroom');self.assertEqual(value['excludedMedia'][0]['approval'],'geometry-study')
        all_value=query(self.catalog,self.root,'bathroom','all');self.assertEqual(len(all_value['media']),2)
        self.assertFalse(next(m for m in all_value['media'] if m['path']=='docs/draft.png')['usableForChapter'])

    def test_incremental_reuses_then_updates(self):
        result=build(self.root,self.index);self.assertEqual(result['timing']['changedDocuments'],0)
        write_json(self.root,'docs/generation.json',{'status':'changed'})
        result=build(self.root,self.index);self.assertEqual(result['timing']['changedDocuments'],1)

    def test_query_never_network(self):
        with patch('subprocess.run',side_effect=AssertionError('network forbidden')):
            query(self.catalog,self.root,'bathroom')

    def test_metadata_query_never_probes_media(self):
        with patch('query.media_path',side_effect=AssertionError('media probe forbidden')):
            value=query(self.catalog,self.root,'bathroom')
        self.assertEqual(value['media'][0]['availability'],'not-probed')

    def test_shared_ids_metadata_never_stats_storage(self):
        from storage_bridge import annotate
        row={'sha256':'a'*64,'bytes':10}
        bridge={'namespace':'replica-store-v1/book-art','assetsBySha256':{'a'*64:[{'assetId':'existing-id','bytes':10,'storagePath':'assets/x.png'}]}}
        with patch('storage_bridge.inside',side_effect=AssertionError('storage probe forbidden')):
            annotate(self.root,row,bridge)
        self.assertEqual(row['sharedReplica']['registeredStudioIds'],['existing-id'])
        self.assertIsNone(row['sharedReplica']['localOwnedPresent'])

    def test_registered_shared_source_fallback_no_network(self):
        from storage_bridge import resolve
        data=self.base/'studio';(data/'assets').mkdir(parents=True)
        path=data/'assets/book.png';path.write_bytes(self.book)
        sha=hashlib.sha256(self.book).hexdigest()
        bridge={'assetsBySha256':{sha:[{'assetId':'book-id','bytes':len(self.book),'storagePath':'assets/book.png'}]}}
        with patch('storage_bridge.repository',return_value=(object(),{},data)),patch('subprocess.run',side_effect=AssertionError('network forbidden')):
            actual=resolve(self.root,bridge,{'sha256':sha,'bytes':len(self.book)})
        self.assertEqual(actual,path)

    def test_unwired_assets_not_silently_allowlisted(self):
        value=query(self.catalog,self.root,'bathroom','all')
        self.assertTrue(all(m['studioAllowlisted'] is False for m in value['media']))

    def test_hydrate_local_hashes_and_default_no_network(self):
        manifest=query(self.catalog,self.root,'bathroom')
        with patch('subprocess.run',side_effect=AssertionError('network forbidden')):
            result=hydrate(self.root,manifest,self.base/'bundle',1024)
        self.assertEqual(result['verifiedPaths'],['docs/book.png'])
        self.assertFalse(result['restore']['networkInvoked'])
        self.assertEqual((self.base/'bundle/media/docs/book.png').read_bytes(),self.book)

    def test_missing_creates_subset_without_download(self):
        (self.root/'docs/book.png').unlink();manifest=query(self.catalog,self.root,'bathroom')
        with patch('subprocess.run',side_effect=AssertionError('network forbidden')):
            result=hydrate(self.root,manifest,self.base/'missing-bundle',1024)
        self.assertEqual(len(result['missing']),1)
        restore=json.loads((self.base/'missing-bundle/restore-manifest.json').read_text())
        self.assertEqual([r['path'] for r in restore['assets']],['docs/book.png'])

    def test_budget_prevents_copy_or_download(self):
        manifest=query(self.catalog,self.root,'bathroom')
        with patch('subprocess.run',side_effect=AssertionError('network forbidden')):
            with self.assertRaises(LocationError):hydrate(self.root,manifest,self.base/'small',1,restore=True)
        self.assertFalse((self.base/'small').exists())

    def test_corrupt_source_rejected(self):
        manifest=query(self.catalog,self.root,'bathroom');(self.root/'docs/book.png').write_bytes(b'corruption')
        with self.assertRaises(LocationError):hydrate(self.root,manifest,self.base/'bad',1024)

    def test_output_inside_source_rejected(self):
        with self.assertRaises(LocationError):external_path(self.root,self.root/'bundle')

    def test_output_symlink_rejected(self):
        target=self.base/'target';target.mkdir();(self.base/'link').symlink_to(target,target_is_directory=True)
        with self.assertRaises(LocationError):external_path(self.root,self.base/'link/output')

    def test_metadata_symlink_escape_rejected(self):
        (self.root/'escape.json').symlink_to(self.index)
        with self.assertRaises(LocationError):metadata_path(self.root,'escape.json')

    def test_path_traversal_rejected(self):
        with self.assertRaises(LocationError):query(self.catalog,self.root,'../bathroom')
        with self.assertRaises(LocationError):media_path(self.root,'../outside.png')

    def test_cli_unknown_structured_error(self):
        result=subprocess.run([sys.executable,'-B',str(MODULES/'cli.py'),'--root',str(self.root),'--index',str(self.index),'query','unknown'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stdout)['error']['code'],'location_request_rejected')

    def test_stop_requires_orbit_and_valid_range(self):
        with self.assertRaises(LocationError):query(self.catalog,self.root,'bathroom',stop='stop-24')


if __name__=='__main__':unittest.main()
