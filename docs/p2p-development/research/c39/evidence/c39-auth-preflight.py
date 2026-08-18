#!/usr/bin/env python3
"""C39 auth preflight (READ-ONLY, presence-only).
Classifies Manus / Hermes / Codex current auth states without printing values.
"""
import json, os, subprocess, sys

REPORT = {}

def classify(name, status):
    REPORT[name] = status
    print(f"{name}: {status}")

# --- Manus ---
key_file = os.path.expanduser('/home/ubuntu/.secrets/manus_api_key')
if os.path.exists(key_file):
    with open(key_file) as f:
        key = f.read().strip()
    if not key:
        classify('Manus', 'AUTH_INVALID')
        sys.exit()
    # probe task.list (presence only)
    import urllib.request
    try:
        req = urllib.request.Request('https://api.manus.ai/v2/tasks?page_size=1',
                                     headers={'x-manus-api-key': key})
        with urllib.request.urlopen(req, timeout=30) as r:
            code = r.status
            body = r.read()
            if code == 200 and body:
                classify('Manus', 'AUTH_VALID')
            else:
                classify('Manus', 'AUTH_INVALID')
    except urllib.error.HTTPError as e:
        classify('Manus', 'AUTH_INVALID')
    except Exception:
        classify('Manus', 'AUTH_INVALID')
else:
    classify('Manus', 'AUTH_ABSENT')

# --- Hermes (binary + gemini key) ---
import shutil
hermes = shutil.which('hermes')
gm = os.path.exists('/home/ubuntu/.secrets/gemini_api_key') or any(
    n.startswith('gemini') for n in os.listdir('/home/ubuntu/.secrets')
)
if hermes and gm:
    # non-mutating probe: capital of Vietnam with a timeout; report presence-only
    key = ''
    for n in os.listdir('/home/ubuntu/.secrets'):
        if 'gemini' in n:
            with open(os.path.join('/home/ubuntu/.secrets', n)) as f:
                key = f.read().strip()
    env = os.environ.copy()
    env['GEMINI_API_KEY'] = key
    try:
        r = subprocess.run([hermes, 'agent', 'run', '--once',
                            '-m', 'Answer with exactly one word, the capital of Vietnam.',
                            '-p', 'gemini'], capture_output=True, text=True,
                           env=env, timeout=120)
        out = (r.stdout + r.stderr).lower()
        if r.returncode == 0 and ('hanoi' in out or 'hà nội' in out or 'hano' in out):
            classify('Hermes', 'AUTH_VALID')
        else:
            classify('Hermes', f'AUTH_INVALID(rc={r.returncode})')
    except subprocess.TimeoutExpired:
        classify('Hermes', 'AUTH_UNKNOWN(runtime probe timeout)')
    except Exception as e:
        classify('Hermes', 'AUTH_ABSENT')
elif hermes:
    classify('Hermes', 'AUTH_ABSENT')  # binary present, no credential
else:
    classify('Hermes', 'AUTH_ABSENT')

# --- Codex ---
codex = shutil.which('codex')
if codex:
    try:
        r = subprocess.run([codex, '--version'], capture_output=True, text=True, timeout=30)
        classify('Codex', 'AUTH_VALID' if r.returncode == 0 else 'AUTH_INVALID')
    except Exception:
        classify('Codex', 'AUTH_UNKNOWN')
else:
    classify('Codex', 'AUTH_ABSENT')

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c39-auth-preflight.json')
with open(path, 'w') as f:
    json.dump(REPORT, f, indent=2)
print('written:', path)
