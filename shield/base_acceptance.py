"""Runtime-only Git metadata fixtures, real pinned providers, durable log evidence (v0.2.0 - 3 controls)."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from shield.osv_acquire import acquire as osv_acquire
from shield.dependency import assess as osv_assess
from shield.profile import evaluate
from shield.runner import assess as secret, resolve_target_ref
from shield import zizmor_acquire
from shield import ci as zizmor_ci

CI_PASS_WORKFLOW = """name: ci
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hello
"""

CI_FAIL_WORKFLOW = """name: ci
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo hello
"""

def emit(label, record):
    text = label + '\n```json\n' + json.dumps(record, indent=2) + '\n```\n'
    print(text, flush=True)
    annotation = json.dumps(record, separators=(',', ':')).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    if 'git_history_scan' not in label and 'worktree_scan' not in label:
        print('::notice title=' + label + '::' + annotation, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(text)

def _ensure_workflow(repo: Path, content: str):
    wf_dir = repo / ".github/workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "ci.yml").write_text(content, encoding="utf-8")

def main():
    reference = os.environ.get('EVIDENCE_REFERENCE', 'local-runtime-test')
    failures = []
    with tempfile.TemporaryDirectory(prefix='shield-base-') as tmp:
        root = Path(tmp)
        osv_binary = root / 'missing-osv'
        ziz_binary = root / 'missing-zizmor'
        ziz_receipt = {}
        # Acquire OSV
        try:
            osv_binary, receipt = osv_acquire(root / 'osv-provider')
            emit('OSV_ACQUISITION=VERIFIED', receipt)
        except Exception as exc:
            emit('OSV_ACQUISITION=BLOCKED', {'reason': type(exc).__name__, 'detail': str(exc)[:200]})
            failures.append('OSV_ACQUISITION_BLOCKED')
        # Acquire Zizmor
        # Prefer env var if provided (hosted workflow sets it), otherwise acquire
        env_ziz = os.environ.get('ZIZMOR_EXECUTABLE')
        if env_ziz and Path(env_ziz).is_file():
            ziz_binary = Path(env_ziz)
            try:
                observed = zizmor_acquire.verify_executable(ziz_binary)
                emit('ZIZMOR_ACQUISITION=VERIFIED', {'provider': 'Zizmor', 'observed_version': observed, 'executable': str(ziz_binary)})
            except Exception as exc:
                emit('ZIZMOR_ACQUISITION=BLOCKED', {'reason': type(exc).__name__, 'detail': str(exc)[:200]})
                failures.append('ZIZMOR_ACQUISITION_BLOCKED')
                ziz_binary = root / 'missing-zizmor'
        else:
            try:
                ziz_binary, ziz_receipt = zizmor_acquire.acquire(root / 'zizmor-provider')
                emit('ZIZMOR_ACQUISITION=VERIFIED', ziz_receipt)
            except Exception as exc:
                emit('ZIZMOR_ACQUISITION=BLOCKED', {'reason': type(exc).__name__, 'detail': str(exc)[:200]})
                failures.append('ZIZMOR_ACQUISITION_BLOCKED')
                ziz_binary = root / 'missing-zizmor'

        # Determine executable for secret
        gitleaks_exec = os.environ.get('GITLEAKS_EXECUTABLE', '')
        if not gitleaks_exec or not Path(gitleaks_exec).is_file():
            # Try to find via previous acquire if workflow didn't set env
            # Fallback: look in runner temp if exists
            pass

        for label, requirement, expected_dep in [('pass', 'idna==3.15', 'PASS'),
                                                ('fail', 'Django==1.11.29', 'FAIL')]:
            repo = root / label
            repo.mkdir()
            (repo / 'requirements.txt').write_text(requirement + '\n')
            # Add CI workflow: keep CI PASS for both dependency pass/fail cases so profile FAIL is due to dependency in second case
            _ensure_workflow(repo, CI_PASS_WORKFLOW)
            for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Shield Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'metadata only')]:
                subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
            secret_records = []
            for scope in ('git_history_scan', 'worktree_scan'):
                e = secret(shield_dir=Path('shield').resolve(), control_id='SHIELD-SECRET-01', scan_mode=scope,
                           target=repo, executable=os.environ.get('GITLEAKS_EXECUTABLE', '/tmp/missing-gitleaks'), provider_mapping=None,
                           timeout=120, reference=reference)
                emit(label + ':' + scope, e)
                secret_records.append(e)
            dep = osv_assess(repo, osv_binary, ['requirements.txt'], reference)
            emit(label + ':dependency', dep)
            ci_evidence = zizmor_ci.assess(repo, ziz_binary, reference)
            emit(label + ':ci', ci_evidence)
            result = evaluate(secret_records + [dep] + [ci_evidence], repo, resolve_target_ref(repo))
            emit(label + ':profile', result)
            if dep['status'] != expected_dep:
                failures.append(label + '_DEPENDENCY_UNPROVEN')
            # For pass case, expect ci PASS as well and profile PASS; for fail case, dependency FAIL => profile FAIL irrespective of CI PASS
            if label == 'pass':
                if ci_evidence['status'] != 'PASS':
                    failures.append('pass_CI_NOT_PASS')
                if result['PROFILE_REQUIREMENTS_STATUS'] != 'PASS':
                    failures.append('pass_PROFILE_NOT_PASS')
            else:
                if result['PROFILE_REQUIREMENTS_STATUS'] != 'FAIL':
                    failures.append('fail_PROFILE_NOT_FAIL')
            if label == 'fail':
                expected_id = 'GHSA-8x94-hmjh-97hq'
                ids = [f['vulnerability_id'] for f in dep['findings']]
                emit('EXPECTED_VULNERABILITY', {'id': expected_id, 'observed': expected_id in ids})
                if expected_id not in ids:
                    failures.append('EXPECTED_VULNERABILITY_NOT_OBSERVED')
            if label == 'pass':
                # Prove BLOCKED on unavailable provider: both dependency and CI unavailable should yield BLOCKED profile
                blocked_dep = osv_assess(repo, root / 'absent-provider', ['requirements.txt'], reference)
                emit('unavailable:dependency', blocked_dep)
                blocked_ci = zizmor_ci.assess(repo, root / 'absent-zizmor', reference)
                emit('unavailable:ci', blocked_ci)
                for name, evidence_list in [
                    ('unavailable_dep', secret_records + [blocked_dep] + [ci_evidence]),
                    ('unavailable_ci', secret_records + [dep] + [blocked_ci]),
                    ('missing_ci', secret_records + [dep]),
                    ('missing_dep', secret_records + [ci_evidence]),
                ]:
                    res = evaluate(evidence_list, repo, resolve_target_ref(repo))
                    emit(name + ':profile', res)
                    if res['PROFILE_REQUIREMENTS_STATUS'] != 'BLOCKED':
                        failures.append(name + '_BLOCKED_UNPROVEN')

        # Additional CI-specific FAIL proof: dependency PASS, CI FAIL => profile FAIL
        repo_cifail = root / 'ci-fail'
        repo_cifail.mkdir()
        (repo_cifail / 'requirements.txt').write_text('idna==3.15\n')
        _ensure_workflow(repo_cifail, CI_FAIL_WORKFLOW)
        for args in [('init', '-q'), ('add', '.'), ('-c', 'user.name=Shield Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'metadata only')]:
            subprocess.run(['git', '-C', str(repo_cifail), *args], check=True, capture_output=True)
        secret_records_cf = []
        for scope in ('git_history_scan', 'worktree_scan'):
            e = secret(shield_dir=Path('shield').resolve(), control_id='SHIELD-SECRET-01', scan_mode=scope,
                       target=repo_cifail, executable=os.environ.get('GITLEAKS_EXECUTABLE', '/tmp/missing-gitleaks'), provider_mapping=None,
                       timeout=120, reference=reference)
            secret_records_cf.append(e)
        dep_cf = osv_assess(repo_cifail, osv_binary, ['requirements.txt'], reference)
        ci_cf = zizmor_ci.assess(repo_cifail, ziz_binary, reference)
        emit('ci-fail:dependency', dep_cf)
        emit('ci-fail:ci', ci_cf)
        if ci_cf['status'] != 'FAIL':
            failures.append('CI_FAIL_CASE_NOT_FAIL')
            emit('CI_FAIL_DETECTED', {'expected': 'FAIL', 'observed': ci_cf['status']})
        else:
            # Check that audit identifier is present
            audits = [f.get('audit') for f in ci_cf.get('findings',[])]
            emit('CI_FAIL_AUDIT', {'audits': audits})
            if 'unpinned-uses' not in audits:
                failures.append('CI_FAIL_AUDIT_NOT_OBSERVED')
        result_cf = evaluate(secret_records_cf + [dep_cf] + [ci_cf], repo_cifail, resolve_target_ref(repo_cifail))
        emit('ci-fail:profile', result_cf)
        if result_cf['PROFILE_REQUIREMENTS_STATUS'] != 'FAIL':
            failures.append('CI_FAIL_PROFILE_NOT_FAIL')
        # Also prove BLOCKED for target not git repo for CI
        plain = root / 'plain-dir'
        plain.mkdir()
        (plain / 'README.md').write_text('not a repo')
        blocked_plain = zizmor_ci.assess(plain, ziz_binary, reference)
        emit('plain_not_git:ci', blocked_plain)
        if blocked_plain['status'] != 'BLOCKED':
            failures.append('CI_PLAIN_NOT_GIT_NOT_BLOCKED')

        emit('SLICE2_3_ACCEPTANCE', {'result': 'BLOCKED' if failures else 'PASS', 'unproven': failures,
                                   'SYSTEM_SECURITY_VERDICT': 'NOT_EVALUATED'})
    return 2 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
