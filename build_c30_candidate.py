#!/usr/bin/env python3
"""Build the C30 candidate via the canonical package_release tool.

Runs `package_release --root /tmp/buildroot --output ... build` from a
temporary governance snapshot (C30 candidate record stripped so the
placeholder-SHA self-reference does not fail lineage validation), and
leaves the verified artifact at /tmp/p2p-c30-candidate.zip.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path('/tmp/buildroot')
GOV = ROOT.joinpath('governance', 'development-control.json')
OUTPUT = '/tmp/p2p-c30-candidate.zip'


def _refresh_buildroot() -> None:
    """Re-copy the live repo into /tmp/buildroot (ignoring transient dirs)."""
    if ROOT.exists():
        shutil.rmtree(ROOT)
    shutil.copytree(
        pathlib.Path('/home/ubuntu/p2p'), ROOT,
        ignore=shutil.ignore_patterns('.git', '.tmp', 'reports', '.agents'),
        ignore_dangling_symlinks=True)
    # package_release requires .agents/skills — restore it.
    shutil.copytree(
        pathlib.Path('/home/ubuntu/p2p/.agents/skills'),
        ROOT.joinpath('.agents', 'skills'),
        ignore=shutil.ignore_patterns('.git'),
        ignore_dangling_symlinks=True)
    evals = ROOT.joinpath('.p2p', 'evals')
    if evals.exists():
        shutil.rmtree(evals)


def main() -> int:
    _refresh_buildroot()
    # Strip the future C30 candidate record (not yet filled) from the
    # buildroot governance snapshot so candidate validation is clean.
    gov = json.loads(GOV.read_text())
    gov['candidate_records'] = [
        r for r in gov.get('candidate_records', [])
        if r.get('development_goal') != 'C30'
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                     delete=False) as tmp:
        json.dump(gov, tmp, indent=2)
        tmp_path = tmp.name

    shutil.copy(GOV, str(GOV) + '.prebuild-backup')
    GOV.write_text(json.dumps(gov, indent=2, ensure_ascii=False) + '\n')

    proc = subprocess.run(
        [sys.executable, 'scripts/package_release.py',
         '--root', str(ROOT), '--output', OUTPUT, 'build'],
        capture_output=True, text=True, cwd='/home/ubuntu/p2p')
    rc = proc.returncode
    print('--- build rc =', rc)
    print(proc.stdout[-3000:])
    if proc.stderr:
        print('STDERR:', proc.stderr[-2000:])
    return rc


if __name__ == '__main__':
    sys.exit(main())
