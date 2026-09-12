import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from shield import osv_acquire as osv
from shield.dependency import inventory, parse_report, assess
from shield.profile import evaluate, PROFILE


class BaseSlice(unittest.TestCase):
    def records(self):
        return [dict(schema='p2p-shield-evidence/1', control_id=c, control_version='0.1.0',
                     scope=s, target='/fixture', target_ref='a'*40, timestamp='2026-09-12T00:00:00Z',
                     status='PASS', findings_count=0, coverage=['assessed'], limitations=[],
                     provider='provider', provider_version='1', provider_source='upstream@tag',
                     reason='assessed', artifact_or_reference='run')
                for c, rule in PROFILE['required_controls'].items() for s in rule['required_scopes']]

    def test_control_contract(self):
        c = json.loads(Path('shield/controls/SHIELD-DEPENDENCY-01.json').read_text())
        for field in ('control_id', 'control_version', 'objective', 'applies_to', 'required_scope', 'required_evidence', 'limitations'):
            self.assertTrue(c[field])
        self.assertEqual(set(c['status_semantics']), {'PASS','FAIL','BLOCKED'})
        self.assertEqual(set(PROFILE['required_controls']), {'SHIELD-SECRET-01','SHIELD-DEPENDENCY-01','SHIELD-CI-01'})

    def test_source_and_version_pins(self):
        original = osv.mapping()
        for key, val in [('provider_version','2.5.0'),('provider_version','2.5.1'),('provider_version','latest'),('provider_name','Other')]:
            m = copy.deepcopy(original); m[key] = val
            with patch.object(Path, 'read_text', return_value=json.dumps(m)), self.assertRaises(ValueError):
                osv.mapping()
        for key, val in [('repository','mirror/osv-scanner'), ('tag','v2.5.0'), ('asset','elsewhere')]:
            m = copy.deepcopy(original); m['source'][key] = val
            with patch.object(Path, 'read_text', return_value=json.dumps(m)), self.assertRaises(ValueError):
                osv.mapping()

    def test_exact_observed_version(self):
        import subprocess
        for text, valid in [('osv-scanner version: 2.4.0\n',True),('2.4.00',False),('2.4.0-dev',False),('2.5.1',False)]:
            with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([],0,text,'')):
                if valid: self.assertEqual(osv.version('binary'),'2.4.0')
                else:
                    with self.assertRaises(ValueError): osv.version('binary')

    def test_checksum(self):
        data = b'unit-test-only'
        digest = hashlib.sha256(data).hexdigest()
        line = digest + '  ' + osv.ASSET
        self.assertEqual(osv.verify_checksum(data,line),digest)
        for bad in ['',line+ '\n'+line, '0'*64+'  '+osv.ASSET]:
            with self.assertRaises(ValueError): osv.verify_checksum(data,bad)

    def test_pass_fail_and_indeterminate_output(self):
        expected = {'/fixture/requirements.txt': {('idna','3.10')}}
        report = {'results':[{'source':{'path':'/fixture/requirements.txt','type':'lockfile'},'packages':[
            {'package':{'name':'idna','version':'3.10','ecosystem':'PyPI'}}]}]}
        self.assertEqual(parse_report(report,0,expected),[])
        fail = copy.deepcopy(report)
        fail['results'][0]['packages'][0]['vulnerabilities'] = [{'id':'TEST-ADVISORY'}]
        self.assertEqual(len(parse_report(fail,1,expected)),1)
        for doc, rc in [(report,2),(report,1),(fail,0),({},0),({'results':[]},0)]:
            with self.assertRaises(ValueError): parse_report(doc,rc,expected)

    def test_inventory_and_unavailable_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for text in ['', 'Django>=1', '-r other.txt', 'https://private.example/token']:
                (root/'requirements.txt').write_text(text)
                with self.assertRaises(ValueError): inventory(root,['requirements.txt'])
            (root/'requirements.txt').write_text('idna==3.10\n')
            with patch('shield.dependency.resolve_target_ref',return_value='a'*40):
                self.assertEqual(assess(root,root/'absent',['requirements.txt'],'run')['status'],'BLOCKED')

    def test_profile_pass_fail_blocked_no_overclaim(self):
        for status in ['PASS','FAIL','BLOCKED']:
            records = self.records()
            records[-1].update(status=status, findings_count=1 if status=='FAIL' else 0)
            result=evaluate(records,'/fixture','a'*40)
            self.assertEqual(result['PROFILE_REQUIREMENTS_STATUS'],status)
            self.assertEqual(result['SYSTEM_SECURITY_VERDICT'],'NOT_EVALUATED')
            self.assertNotIn('SYSTEM_SECURE',result)

    def test_missing_mismatch_malformed_duplicate_evidence(self):
        for field,value in [('control_id','OTHER'),('control_version','9'),('target_ref','b'*40),('target','/other'),('schema','x'),('timestamp','bad'),('coverage',[]),('findings_count',True)]:
            records=self.records(); records[-1][field]=value
            self.assertEqual(evaluate(records,'/fixture','a'*40)['PROFILE_REQUIREMENTS_STATUS'],'BLOCKED')
        for records in [self.records()[:-1],self.records()+[self.records()[0]],[],[{}]]:
            self.assertEqual(evaluate(records,'/fixture','a'*40)['PROFILE_REQUIREMENTS_STATUS'],'BLOCKED')


if __name__ == '__main__': unittest.main()
