"""Offline safety/reliability tests. No network requests or real inferences."""
import contextlib,importlib.util,io,json,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('heldout_runner',Path(__file__).with_name('run_live.py'));runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
class Response:
 status=202
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self):return b'{"id":"run_test","status":"running"}'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);(self.p/'test.png').write_bytes(b'offline test bytes');(self.p/'manifest.sha256').write_text('testhash  manifest.json\n')
  self.manifest={'target':'https://example.invalid/','model_profile':'test','run_order':[{'case_id':'test','guard_enabled':True},{'case_id':'test','guard_enabled':False}],'cases':[{'id':'test','image':'test.png','sha256':'fake','request':'Read only','scenario':'test'}]}
  self.stack=contextlib.ExitStack();self.stack.enter_context(patch.object(runner,'P',self.p));self.stack.enter_context(patch.object(runner,'verify',return_value=self.manifest));self.stack.enter_context(patch('sys.stdout',new=io.StringIO()));self.stack.enter_context(patch.object(runner.time,'sleep'))
 def tearDown(self):self.stack.close();self.tmp.cleanup()
 def invoke(self,args):
  with patch('sys.argv',['run_live.py']+args):runner.main()
 def test_default_never_networks(self):
  with patch.object(runner.urllib.request,'urlopen') as post:
   self.invoke([]);post.assert_not_called()
  self.assertFalse((self.p/'runs').exists())
 def test_404_stops_before_next_post(self):
  with patch.object(runner.urllib.request,'urlopen',return_value=Response()) as post,patch.object(runner,'get_json',side_effect=urllib.error.HTTPError('https://example.invalid/',404,'Not Found',None,None)):
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   self.assertEqual(post.call_count,1)
  e=json.loads((self.p/'runs/test_on_observation_error.json').read_text());self.assertEqual(e['observation_status'],'inconclusive');self.assertEqual(e['reason'],'nonretryable_http_404')
 def test_deadline_stops_without_retry(self):
  with patch.object(runner.urllib.request,'urlopen',return_value=Response()) as post,patch.object(runner.time,'monotonic',side_effect=[0,0,601]),patch.object(runner,'get_json') as get:
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   self.assertEqual(post.call_count,1);get.assert_not_called()
  e=json.loads((self.p/'runs/test_on_observation_error.json').read_text());self.assertEqual(e['reason'],'poll_deadline')
 def test_uncertain_post_not_repeated(self):
  with patch.object(runner.urllib.request,'urlopen',side_effect=urllib.error.URLError('uncertain submission')) as post:
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   self.assertEqual(post.call_count,1)
  self.assertTrue((self.p/'runs/test_on_request.json').exists());e=json.loads((self.p/'runs/test_on_submission_error.json').read_text());self.assertFalse(e['post_retried'])
 def test_submission_403_stops_all_later_posts(self):
  error=urllib.error.HTTPError('https://example.invalid/',403,'Forbidden',None,None)
  with patch.object(runner.urllib.request,'urlopen',side_effect=error) as post:
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   self.assertEqual(post.call_count,1)
  self.assertFalse((self.p/'runs/test_off_request.json').exists())
  e=json.loads((self.p/'runs/test_on_submission_error.json').read_text());self.assertEqual(e['http_status'],403)
 def test_interrupted_post_blocks_restart_without_retry_or_later_posts(self):
  with patch.object(runner.urllib.request,'urlopen',side_effect=KeyboardInterrupt) as post:
   with self.assertRaises(KeyboardInterrupt):self.invoke(['--execute-live'])
   with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
   self.assertEqual(post.call_count,1)
  self.assertFalse((self.p/'runs/test_off_request.json').exists())
 def test_invalid_terminal_record_blocks_restart(self):
  out=self.p/'runs';out.mkdir();(out/'test_on_request.json').write_text('{}')
  for terminal in ('not JSON','[]','{"id":"run_test","status":"running"}'):
   (out/'test_on.json').write_text(terminal)
   with patch.object(runner.urllib.request,'urlopen') as post:
    with self.assertRaises(SystemExit):self.invoke(['--execute-live'])
    post.assert_not_called()
if __name__=='__main__':unittest.main()
