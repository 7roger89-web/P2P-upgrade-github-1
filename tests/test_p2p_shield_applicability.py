import copy, os, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from shield import ci
from shield.profile import evaluate, PROFILE
from shield.runner import resolve_target_ref

def init(r):
 e={**os.environ,'GIT_AUTHOR_NAME':'f','GIT_AUTHOR_EMAIL':'f@x','GIT_COMMITTER_NAME':'f','GIT_COMMITTER_EMAIL':'f@x','GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_SYSTEM':os.devnull}; subprocess.run(['git','init','-q'],cwd=r,check=True,env=e); subprocess.run(['git','add','-A'],cwd=r,check=True,env=e); subprocess.run(['git','-c','commit.gpgsign=false','commit','-qm','f'],cwd=r,check=True,env=e)
class T(unittest.TestCase):
 def setUp(self): self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.root=Path(self.t.name)
 def repo(self,w=False):
  r=self.root/('w' if w else 'e'); r.mkdir(); (r/'README.md').write_text('x')
  if w: d=r/'.github/workflows'; d.mkdir(parents=True); (d/'ci.yml').write_text('name: ci\non: push\njobs:\n  x:\n    runs-on: ubuntu-latest\n    steps: []\n')
  init(r); return r
 def records(self,r,c):
  ref=resolve_target_ref(r); out=[]
  for cid,rule in PROFILE['required_controls'].items():
   for scope in rule['required_scopes']:
    out.append(c if cid=='SHIELD-CI-01' else dict(schema='p2p-shield-evidence/1',control_id=cid,control_version=rule['control_version'],scope=scope,target=str(r),target_ref=ref,timestamp='2026-09-15T00:00:00Z',status='PASS',findings_count=0,coverage=['assessed'],limitations=[],provider='p',provider_version='1',provider_source='u@t',reason='assessed',artifact_or_reference='run'))
  return out
 def test_na_passes_profile_only_for_empty_inventory(self):
  r=self.repo();
  with patch('shield.ci.zizmor_acquire.verify_executable',side_effect=AssertionError('provider must not run')): e=ci.assess(r,self.root/'missing','run')
  self.assertEqual(e['status'],'NOT_APPLICABLE'); q=evaluate(self.records(r,e),r,resolve_target_ref(r)); self.assertEqual(q['PROFILE_REQUIREMENTS_STATUS'],'PASS'); self.assertEqual(q['NOT_APPLICABLE_CONTROLS'],['SHIELD-CI-01']); self.assertEqual(q['SYSTEM_SECURITY_VERDICT'],'NOT_EVALUATED')
 def test_forged_na_blocked(self):
  r=self.repo(); e=ci.assess(r,self.root/'missing','run')
  for m in ({'coverage':['x']},{'findings_count':1},{'reason':'x'},{'applicability':{'basis':'x','path':'.github/workflows','workflow_count':0}}):
   f=copy.deepcopy(e); f.update(m); self.assertEqual(evaluate(self.records(r,f),r,resolve_target_ref(r))['PROFILE_REQUIREMENTS_STATUS'],'BLOCKED')
 def test_applicable_missing_provider_stays_blocked(self):
  r=self.repo(True); e=ci.assess(r,self.root/'missing','run'); self.assertEqual(e['status'],'BLOCKED'); self.assertEqual(evaluate(self.records(r,e),r,resolve_target_ref(r))['PROFILE_REQUIREMENTS_STATUS'],'BLOCKED')
