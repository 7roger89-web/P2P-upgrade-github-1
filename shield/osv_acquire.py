"""OSV-only official binary acquisition; no changes to Slice-1 trust gates."""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen

VERSION = '2.4.0'
REPOSITORY = 'google/osv-scanner'
ASSET = 'osv-scanner_linux_amd64'
SOURCE = {'kind': 'official_github_release', 'repository': REPOSITORY,
          'tag': 'v2.4.0', 'asset': ASSET, 'checksums_asset': 'osv-scanner_SHA256SUMS'}
MAPPING = Path(__file__).parent / 'providers/osv-scanner-2.4.0.json'


def mapping():
    m = json.loads(MAPPING.read_text())
    if (m['source'] != SOURCE or m['provider_name'] != 'OSV-Scanner'
            or m['provider_version'] != VERSION or m['failure_behavior'] != 'BLOCKED'
            or m['control_id'] != 'SHIELD-DEPENDENCY-01'):
        raise ValueError('OSV_SOURCE_VERSION_IDENTITY_MISMATCH')
    return m


def version(executable):
    p = subprocess.run([str(executable), '--version'], capture_output=True, text=True, timeout=30)
    if p.returncode or not re.search(r'(?<!\S)v?2\.4\.0(?!\S)', p.stdout + p.stderr):
        raise ValueError('OSV_VERSION_MISMATCH')
    return VERSION


def verify_checksum(data, checksums):
    matches = [line.split()[0] for line in checksums.splitlines()
               if len(line.split()) == 2 and line.split()[1].lstrip('*') == ASSET]
    digest = hashlib.sha256(data).hexdigest()
    if matches != [digest]:
        raise ValueError('OSV_CHECKSUM_MISMATCH_OR_AMBIGUOUS')
    return digest


def acquire(directory):
    mapping()
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / ASSET
    binary.unlink(missing_ok=True)
    base = f'https://github.com/{REPOSITORY}/releases/download/v{VERSION}'
    with urlopen(base + '/osv-scanner_SHA256SUMS', timeout=120) as r:
        checksums = r.read().decode()
    with urlopen(base + '/' + ASSET, timeout=120) as r:
        data = r.read()
    digest = verify_checksum(data, checksums)
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        staged = Path(tmp) / ASSET
        staged.write_bytes(data)
        staged.chmod(0o700)
        observed = version(staged)
        staged.replace(binary)
    receipt = dict(source=SOURCE, sha256=digest, observed_version=observed)
    binary.with_suffix('.verified.json').write_text(json.dumps(receipt))
    return binary, receipt


def verify_executable(binary):
    mapping()
    receipt = json.loads(binary.with_suffix('.verified.json').read_text())
    if (receipt['source'] != SOURCE or receipt['observed_version'] != VERSION
            or receipt['sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest()):
        raise ValueError('OSV_VERIFIED_EXECUTABLE_MISMATCH')
    return version(binary)
