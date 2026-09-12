"""Narrow declared PyPI metadata scan. No installation or generic parser."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
from shield import osv_acquire
from shield.runner import resolve_target_ref


def inventory(target, manifests):
    result = {}
    for name in manifests:
        path = target / name
        if (path.is_symlink() or not path.resolve().is_relative_to(target)
                or path.name != 'requirements.txt' or not path.is_file()):
            raise ValueError('UNSUPPORTED_MANIFEST')
        entries = []
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)', line.strip())
            if not match:
                raise ValueError('INDETERMINATE_INVENTORY')
            entries.append((re.sub(r'[-_.]+', '-', match[1]).lower(), match[2]))
        if not entries or str(path.resolve()) in result:
            raise ValueError('EMPTY_OR_DUPLICATE_INVENTORY')
        result[str(path.resolve())] = set(entries)
    if not result:
        raise ValueError('MISSING_INVENTORY')
    return result


def parse_report(report, rc, expected):
    if rc not in (0, 1) or not isinstance(report, dict) or not isinstance(report.get('results'), list):
        raise ValueError('PROVIDER_EXECUTION_OR_OUTPUT_FAILURE')
    seen, findings = {}, []
    for source in report['results']:
        path = source['source']['path']
        if path not in expected or source['source']['type'] != 'lockfile' or path in seen:
            raise ValueError('SOURCE_SCOPE_MISMATCH')
        seen[path] = set()
        for entry in source['packages']:
            p = entry['package']
            if p['ecosystem'] != 'PyPI':
                raise ValueError('ECOSYSTEM_MISMATCH')
            seen[path].add((re.sub(r'[-_.]+', '-', p['name']).lower(), p['version']))
            vulns = entry.get('vulnerabilities', [])
            if not isinstance(vulns, list):
                raise ValueError('MALFORMED_FINDINGS')
            for v in vulns:
                if not isinstance(v.get('id'), str) or not v['id']:
                    raise ValueError('MALFORMED_FINDING_ID')
                findings.append(dict(vulnerability_id=v['id'], package=p['name'], ecosystem=p['ecosystem'], version=p['version'], manifest=path))
    if seen != expected or bool(findings) != (rc == 1):
        raise ValueError('INCOMPLETE_INVENTORY_OR_EXIT_MISMATCH')
    return findings


def assess(target, executable, manifests, reference):
    target, executable = Path(target).resolve(), Path(executable).resolve()
    e = dict(schema='p2p-shield-evidence/1', control_id='SHIELD-DEPENDENCY-01', control_version='0.1.0',
             provider='OSV-Scanner', provider_version='2.4.0', provider_source='google/osv-scanner@v2.4.0',
             target=str(target), target_ref='UNRESOLVED', timestamp=datetime.now(timezone.utc).isoformat(),
             status='BLOCKED', scope='declared_dependency_scan', coverage=['NONE_ESTABLISHED'],
             findings_count=0, findings=[], limitations=[], reason='NOT_ASSESSED', artifact_or_reference=reference,
             declared_manifests=manifests)
    try:
        m = osv_acquire.mapping()
        e['limitations'] = m['limitations'] + m['known_exclusions']
        e['target_ref'] = resolve_target_ref(target)
        if not re.fullmatch('[0-9a-f]{40,64}', e['target_ref']):
            raise ValueError('TARGET_REF_UNRESOLVED')
        expected = inventory(target, manifests)
        e['provider_version_observed'] = osv_acquire.verify_executable(executable)
        with tempfile.TemporaryDirectory() as tmp:
            # Isolate OSV config discovery from target-controlled ignore rules.
            args = [str(executable), 'scan', 'source', '--format=json', '--all-packages', '--no-resolve']
            for path in expected:
                args += ['--lockfile', path]
            config = Path(tmp) / 'osv-scanner.toml'
            config.write_text('')
            args += ['--config', str(config)]
            p = subprocess.run(args, cwd=tmp, capture_output=True, text=True, timeout=180)
            findings = parse_report(json.loads(p.stdout), p.returncode, expected)
        if inventory(target, manifests) != expected or resolve_target_ref(target) != e['target_ref']:
            raise ValueError('TARGET_CHANGED_DURING_SCAN')
        e.update(status='FAIL' if findings else 'PASS', findings=findings, findings_count=len(findings),
                 coverage=m['coverage'], reason='DECLARED_INVENTORY_ASSESSED')
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        e['reason'] = 'ASSESSMENT_BLOCKED:' + type(exc).__name__
        if isinstance(exc, ValueError) and str(exc).isupper():
            e['reason'] += ':' + str(exc)
    return e


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--target', required=True)
    p.add_argument('--executable', required=True)
    p.add_argument('--manifest', action='append', required=True)
    p.add_argument('--reference', required=True)
    a = p.parse_args()
    evidence = assess(a.target, a.executable, a.manifest, a.reference)
    print(json.dumps(evidence, indent=2))
    raise SystemExit({'PASS': 0, 'FAIL': 1, 'BLOCKED': 2}[evidence['status']])
