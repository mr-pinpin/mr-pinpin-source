"""Concurrent recorder integration: originals and every provenance entry survive."""
import concurrent.futures,json,subprocess,tempfile,unittest
from pathlib import Path
class Recording(unittest.TestCase):
 def test_independent_completions_preserve_all_records(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);pack=root/'docs/storyboard/production/test';pack.mkdir(parents=True)
   recorder=pack/'record-image.py';recorder.write_bytes(Path(__file__).with_name('record-image.py').read_bytes())
   prompt=root/'prompt.txt';prompt.write_text('Recorded exact prompt for integration fixture.\n')
   def record(i):
    # Arbitrary bytes exercise preservation; no visual-generation claim is made.
    original=root/f'original-{i}.png';original.write_bytes(f'original bytes {i}'.encode())
    return subprocess.run(['python3',str(recorder),f'test-{i}',str(original),str(prompt),'--review','test fixture'],capture_output=True,text=True)
   with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(record,range(16)))
   for result in results:self.assertEqual(result.returncode,0,result.stderr)
   records=json.loads((pack/'generation-records.json').read_text());self.assertEqual(len(records),16);self.assertEqual(len({r['id'] for r in records}),16)
   for r in records:self.assertEqual((root/r['nativePath']).read_bytes(),Path(r['toolOriginal']).read_bytes())
if __name__=='__main__':unittest.main()
