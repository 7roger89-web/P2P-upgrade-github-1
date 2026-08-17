import re, subprocess

out = subprocess.run(
    ["python3", "-m", "pytest", "tests/test_p2p_execution_target.py",
     "--tb=line", "-q"], capture_output=True, text=True, cwd="/home/ubuntu/p2p"
).stdout + subprocess.run(
    ["python3", "-m", "pytest", "tests/test_p2p_execution_target.py",
     "--tb=line", "-q"], capture_output=True, text=True, cwd="/home/ubuntu/p2p"
).stderr

for m in re.finditer(r"FAILED (\S+) - ?(.*)", out):
    name, msg = m.group(1), m.group(2).strip()
    if msg:
        print(f"{name}\n    -> {msg[:220]}")
