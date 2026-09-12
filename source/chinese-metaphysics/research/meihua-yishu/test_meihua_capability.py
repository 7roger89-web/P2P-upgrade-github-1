#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
p=Path(__file__).with_name('run_meihua_capability.py')
r=subprocess.run([sys.executable,str(p),'--fixture','guanmei'],capture_output=True,text=True)
if r.returncode: print(r.stderr,file=sys.stderr); raise SystemExit(r.returncode)
o=json.loads(r.stdout)
assert o['DOMAIN']=='MEIHUA_YISHU'
assert o['MAIN_HEXAGRAM']=='泽火革' and o['CHANGED_HEXAGRAM']=='泽山咸' and o['MOVING_LINE']==1
assert o['EXTERNAL_SIGN_STATUS']=='MISSING_DO_NOT_FABRICATE'
print('MEIHUA_CAPABILITY_TEST=PASS')
