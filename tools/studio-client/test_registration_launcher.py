import ast,json,os,pathlib,subprocess,sys,tempfile,unittest
WRAPPER=pathlib.Path(__file__).with_name('studio-python')
class LauncherTests(unittest.TestCase):
 def run_script(self,name,code,args=()):
  with tempfile.TemporaryDirectory() as directory:
   script=pathlib.Path(directory)/name; script.write_text(code)
   env={**os.environ,'PINPIN_STUDIO_PYTHON':sys.executable}
   return subprocess.run([str(WRAPPER),str(script),*args],env=env,text=True,capture_output=True,timeout=5),str(script)
 def test_registration_argv_file_import_and_no_site(self):
  result,path=self.run_script('register-image.py','import json,sys,os\nprint(json.dumps([sys.argv,__file__,sys.path[0],sys.flags.no_site]))',['--prompt-file','space $ ` quote\' file','--reference','asset-a'])
  self.assertEqual(result.returncode,0,result.stderr)
  argv,file,directory,no_site=json.loads(result.stdout)
  self.assertEqual(argv,[path,'--prompt-file','space $ ` quote\' file','--reference','asset-a']);self.assertEqual(file,path);self.assertEqual(directory,os.path.dirname(path));self.assertEqual(no_site,1)
 def test_registration_exit_code_preserved(self):
  result,_=self.run_script('register-image.py','raise SystemExit(7)');self.assertEqual(result.returncode,7)
 def test_other_helpers_use_same_script_contract(self):
  result,path=self.run_script('other.py','import json,sys\nprint(json.dumps(sys.argv))',['literal;echo']);self.assertEqual(json.loads(result.stdout),[path,'literal;echo'])
 def test_book_script_runpy_entry(self):
  result,path=self.run_script('book_plan_ops.py','import json,sys\nprint(json.dumps([sys.argv,sys.flags.no_site]))',['context'])
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout),[[path,'context'],1])
 def test_command_mode_preserved(self):
  env={**os.environ,'PINPIN_STUDIO_PYTHON':sys.executable}
  result=subprocess.run([str(WRAPPER),'-c','import sys;print(sys.argv[1])','literal $ ;'],env=env,text=True,capture_output=True,timeout=5)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'literal $ ;')
 def test_setup_uses_prepared_launcher_and_fails_without_it(self):
  import types,hashlib
  source=pathlib.Path(__file__).with_name('register-image.py');tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='setup_toolchain')
  with tempfile.TemporaryDirectory() as directory:
   data=pathlib.Path(directory); launcher=data/'tools/studio-python';launcher.parent.mkdir();launcher.write_text('');launcher.chmod(0o755)
   class Lock:
    def __enter__(self):pass
    def __exit__(self,*args):pass
   store=types.SimpleNamespace(lock=lambda:Lock()); captured={}
   module=types.ModuleType('store');module.atomic_json=lambda path,value:captured.update(value)
   old=sys.modules.get('store');sys.modules['store']=module
   try:
    ns={'Path':pathlib.Path,'os':os,'sys':sys,'hashlib':hashlib,'__file__':str(source),'load_store':lambda args:(store,None,data),'safe_report':lambda data,path:data/path}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
    args=types.SimpleNamespace(runtime_dir=directory,data_dir=None)
    ns['setup_toolchain'](args);self.assertEqual(captured['argvPrefix'][0],str(launcher))
    launcher.unlink()
    with self.assertRaises(ValueError):ns['setup_toolchain'](args)
   finally:
    if old is None:sys.modules.pop('store',None)
    else:sys.modules['store']=old
if __name__=='__main__':unittest.main()
