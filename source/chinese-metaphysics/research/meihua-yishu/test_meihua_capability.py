#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
p=Path(__file__).with_name('run_meihua_capability.py')
def run(args):
    r=subprocess.run([sys.executable,str(p),*args],capture_output=True,text=True)
    if r.returncode: print(r.stderr,file=sys.stderr); raise SystemExit(r.returncode)
    return json.loads(r.stdout)
fixture=run(['--fixture','guanmei'])
assert fixture['DOMAIN']=='MEIHUA_YISHU'
assert fixture['MAIN_HEXAGRAM']=='泽火革' and fixture['CHANGED_HEXAGRAM']=='泽山咸' and fixture['MOVING_LINE']==1
assert fixture['EXTERNAL_SIGN_STATUS']=='MISSING_DO_NOT_FABRICATE'
custom=run(['--lunar-year','2024','--month','12','--day','8','--hour','14'])
assert custom['INPUT_MODE']=='CUSTOM'
assert custom['CASTING_MODE']=='TRADITIONAL_TIME_CASTING'
assert custom['MAIN_HEXAGRAM'] and custom['CHANGED_HEXAGRAM']
assert custom['STRUCTURAL_OUTPUT']=='TI_YONG_RELATION_REPORTED_ONLY'
print('MEIHUA_CAPABILITY_TEST=PASS')
