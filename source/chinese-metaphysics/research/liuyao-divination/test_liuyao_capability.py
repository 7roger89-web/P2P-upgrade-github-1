#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
p=Path(__file__).with_name('run_liuyao_capability.py')
r=subprocess.run([sys.executable,str(p),'--fixture','canonical-01'],capture_output=True,text=True)
if r.returncode: print(r.stderr,file=sys.stderr); raise SystemExit(r.returncode)
o=json.loads(r.stdout)
assert o['DOMAIN']=='LIUYAO'
assert o['BOARD_PACKET']['changed_hexagram']=='地雷复'
assert o['STRUCTURAL_OUTPUT']=='SUPPORT_EXISTS_BUT_SELF_SIDE_CONSTRAINT_PRESENT'
print('LIUYAO_CAPABILITY_TEST=PASS')
