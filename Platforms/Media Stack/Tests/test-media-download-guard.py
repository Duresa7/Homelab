import importlib.util, tempfile, unittest, contextlib, io
from pathlib import Path
guard_path=Path(__file__).resolve().parents[1]/'Scripts'/'media-download-guard.py'
spec=importlib.util.spec_from_file_location('guard',guard_path)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
NOW=1800000000
H='a'*40
class Fake:
 def __init__(self, names=None):
  self.files=[{'name':n,'priority':0 if n.lower().endswith('.exe') else 1} for n in (names if names is not None else ['movie.exe'])]
  self.t={'hash':H,'category':'tv-sonarr','save_path':'/data/downloads/complete','content_path':'/data/downloads/complete/movie.exe','added_on':NOW-300}
  self.rows=[{'id':1,'downloadId':H.upper(),'episodeId':9}]
  self.actions=[];self.throws=False;self.air='2099-01-01T00:00:00Z';self.hasfile=False;self.active=False
 def q(self,path,data=None):
  if path=='app/preferences':return {'excluded_file_names_enabled':True,'excluded_file_names':'*.exe\n*.lnk\n*.bat'}
  if path=='torrents/info':return [self.t] if self.t else []
  if path.startswith('torrents/files'):return self.files
  self.actions.append((path,data))
  if path=='torrents/delete':self.t=None
 def queue(self,app):
  if self.throws:raise RuntimeError('offline')
  return self.rows
 def arr(self,app,path,data=None,method=None):
  if method=='DELETE':self.actions.append(('blocklist',path));self.rows=[];return None
  if path.startswith('episode/'):return {'id':9,'seriesId':1,'monitored':True,'hasFile':self.hasfile,'airDateUtc':self.air}
  if path.startswith('series/'):return {'monitored':True}
  if path=='command':self.actions.append(('search',data));return {'id':42}
  raise AssertionError(path)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=g.State(self.tmp.name)
 def run_guard(self,c,now=NOW,dry=False):
  with contextlib.redirect_stdout(io.StringIO()):g.Guard(c,self.s,now=now).run(dry=dry)
 def test_exe_reject_order_and_persistence(self):
  c=Fake();self.run_guard(c)
  self.assertEqual([a[0] for a in c.actions],['torrents/stop','blocklist','torrents/delete'])
  self.assertIn(H,g.State(self.tmp.name).data['denied'])
 def test_exe_case_and_double_extension(self):
  for name in ['Movie.MKV.EXE','MOVIE.ExE','movie.mkv.exe']:
   self.assertEqual(g.classify([{'name':name}],[]),'blocked_file_type')
 def test_executable_alongside_video_rejected(self):
  self.assertEqual(g.classify([{'name':'film.mkv'},{'name':'codec.exe'}],[]),'blocked_file_type')
 def test_good_video_and_disc_preserved(self):
  for names in [['film.mkv','info.txt'],['film.mkv','sample.zip'],['film.iso'],['unknown.bin']]:
   c=Fake(names);self.run_guard(c);self.assertEqual(c.actions,[])
 def test_archive_without_video_rejected(self):
  for names in [['Show S02E04 1080p WEB H264-CAKES.7z'],['film.ZIP','readme.txt'],['film.rar','film.r00'],['film.part1.rar']]:
   self.assertEqual(g.classify([{'name':n} for n in names],[]),'archive_payload')
 def test_archive_payload_rejected_without_grace(self):
  c=Fake(['Show S02E04 1080p WEB H264-CAKES.7z']);c.t['added_on']=NOW;self.run_guard(c)
  self.assertEqual([a[0] for a in c.actions],['torrents/stop','blocklist','torrents/delete'])
 def test_metadata_pending_preserved(self):
  c=Fake([]);self.run_guard(c);self.assertEqual(c.actions,[])
 def test_no_video_grace(self):
  c=Fake(['readme.txt']);c.t['added_on']=NOW;self.run_guard(c);self.assertEqual(c.actions,[])
  self.run_guard(c,NOW+121);self.assertIsNone(c.t)
 def test_unsafe_paths_never_delete_files(self):
  for name in ['../library/file.exe','/etc/file.exe']:
   self.assertFalse(g.safe_delete({'save_path':'/data/downloads/complete','content_path':'/data/downloads/complete/bad'},[{'name':name}]))
  self.assertFalse(g.safe_delete({'save_path':'/data/media','content_path':'/data/media/file.exe'},[{'name':'file.exe'}]))
 def test_arr_offline_stops_without_deleting(self):
  c=Fake();c.throws=True;self.run_guard(c);self.assertEqual([a[0] for a in c.actions],['torrents/stop'])
 def test_untracked_torrent_waits(self):
  c=Fake();c.rows=[];self.run_guard(c);self.assertIsNotNone(c.t)
  self.run_guard(c,NOW+601);self.assertIsNone(c.t)
 def test_known_hash_without_metadata(self):
  self.s.data['denied'][H]={'reason':'blocked_file_type','first':NOW-1000}
  c=Fake([]);c.rows=[];self.run_guard(c);self.assertIsNone(c.t)
  self.assertEqual(c.actions[-1][1]['deleteFiles'],'false')
 def test_unaired_no_search(self):
  c=Fake();self.run_guard(c);self.assertNotIn('search',[a[0] for a in c.actions])
 def test_retry_limit_and_cooldown(self):
  c=Fake();c.air='2020-01-01T00:00:00Z';self.run_guard(c)
  self.run_guard(c,NOW+60);self.run_guard(c,NOW+1801);self.run_guard(c,NOW+3602)
  self.assertEqual(sum(a[0]=='search' for a in c.actions),2)
 def test_existing_download_no_duplicate_search(self):
  c=Fake();c.t=None;c.air='2020-01-01T00:00:00Z'
  self.s.data['targets']['sonarr:9']={'app':'sonarr','id':9,'attempts':0,'last':0}
  self.run_guard(c);self.assertEqual(c.actions,[])
 def test_imported_file_no_search(self):
  c=Fake();c.hasfile=True;self.run_guard(c);self.assertTrue(self.s.data['targets']['sonarr:9']['done'])
 def test_dry_run_no_mutation(self):
  c=Fake();self.run_guard(c,dry=True);self.assertEqual(c.actions,[]);self.assertEqual(self.s.data['denied'],{})
 def test_manual_category_untouched(self):
  c=Fake();c.t['category']='manual';self.run_guard(c);self.assertEqual(c.actions,[])
 def test_corrupt_state_does_not_reset(self):
  self.s.path.write_text('broken')
  with self.assertRaises(ValueError):g.State(self.tmp.name)
if __name__=='__main__':unittest.main(verbosity=2)
