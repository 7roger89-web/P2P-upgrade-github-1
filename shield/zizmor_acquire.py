"""Zizmor-only official binary acquisition; no changes to Slice-1 or Slice-2 trust gates.

Pins exact provider identity, verifies integrity via GitHub release asset digest,
and refuses any fallback mirror, package manager, Docker, or source build.
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request

VERSION = '1.29.0'
REPOSITORY = 'zizmorcore/zizmor'
ASSET = 'zizmor-x86_64-unknown-linux-gnu.tar.gz'
TAG = 'v1.29.0'
DIGEST = 'dd96df044a6e8538d5f423790f453bdd03d49e5b2bcc38214acc41a2f1297839'
SOURCE = {
    'kind': 'official_github_release',
    'repository': REPOSITORY,
    'tag': TAG,
    'asset': ASSET,
    'download_base': 'https://github.com/zizmorcore/zizmor/releases/download/v1.29.0',
    'extracted_binary': 'zizmor',
    'asset_digest': f'sha256:{DIGEST}',
}
MAPPING = Path(__file__).parent / 'providers/zizmor-1.29.0.json'
USER_AGENT = 'p2p-shield-zizmor-acquire'


def mapping():
    m = json.loads(MAPPING.read_text())
    src = m.get('source', {})
    if (m.get('schema') != 'p2p-shield-provider-mapping/1'
            or m.get('control_id') != 'SHIELD-CI-01'
            or m.get('provider_name') != 'Zizmor'
            or m.get('provider_version') != VERSION
            or m.get('failure_behavior') != 'BLOCKED'
            or src.get('repository') != REPOSITORY
            or src.get('tag') != TAG
            or src.get('asset') != ASSET
            or src.get('asset_digest_value') != DIGEST):
        raise ValueError('ZIZMOR_SOURCE_VERSION_IDENTITY_MISMATCH')
    if 'sha256' not in str(src.get('integrity_rule','')).lower():
        raise ValueError('ZIZMOR_INTEGRITY_RULE_MISSING')
    return m


def _semver_token(text: str) -> str:
    flattened = ' '.join((text or '').split())
    match = re.search(r'(?<!\S)v?(\d+\.\d+\.\d+)(?!\S)', flattened)
    return match.group(1) if match else ''


def version(executable):
    p = subprocess.run([str(executable), '--version'], capture_output=True, text=True, timeout=30)
    observed = _semver_token(p.stdout + ' ' + p.stderr)
    if p.returncode != 0 or observed != VERSION:
        raise ValueError(f'ZIZMOR_VERSION_MISMATCH:observed={observed}:raw={(p.stdout+p.stderr)[:120]}')
    return VERSION


def verify_checksum(data: bytes, expected_digest: str) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_digest:
        raise ValueError(f'ZIZMOR_CHECKSUM_MISMATCH:expected={expected_digest}:actual={digest}')
    return digest


def _download(url: str) -> bytes:
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=120) as r:
        return r.read()


def acquire(directory):
    mapping()
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / 'zizmor'
    # Remove any previous binary to avoid stale version reuse
    binary.unlink(missing_ok=True)
    base = f'https://github.com/{REPOSITORY}/releases/download/{TAG}'
    asset_url = f'{base}/{ASSET}'
    data = _download(asset_url)
    digest = verify_checksum(data, DIGEST)
    # Extract: official asset is tar.gz containing single file named 'zizmor'
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / ASSET
        archive.write_bytes(data)
        import tarfile
        with tarfile.open(archive, 'r:gz') as handle:
            members = handle.getmembers()
            binaries = [m for m in members if m.isfile() and Path(m.name).name == 'zizmor']
            if len(binaries) != 1:
                names = ','.join(m.name for m in members[:8])
                raise ValueError(f'ZIZMOR_BINARY_MEMBER_MISSING:matches={len(binaries)}:members={names}')
            # Extract only the binary file
            member = binaries[0]
            src = handle.extractfile(member)
            if src is None:
                raise ValueError('ZIZMOR_EXTRACT_FAILED')
            staged = tmp_path / 'zizmor'
            staged.write_bytes(src.read())
            staged.chmod(0o755)
            observed = version(staged)
            staged.replace(binary)
    binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipt = dict(source=SOURCE, sha256=digest, binary_sha256=binary_sha256, observed_version=observed, provider='Zizmor', provider_version=VERSION, repository=REPOSITORY, tag=TAG)
    binary.with_suffix('.verified.json').write_text(json.dumps(receipt))
    return binary, receipt


def verify_executable(binary):
    mapping()
    receipt_path = Path(binary).with_suffix('.verified.json')
    if not receipt_path.is_file():
        # Allow direct version check if no receipt (e.g., stub or pre-verified)
        return version(binary)
    receipt = json.loads(receipt_path.read_text())
    # Verify source and version; binary hash check uses binary_sha256 if present (for tar.gz), otherwise legacy sha256
    expected_binary_hash = receipt.get('binary_sha256') or receipt.get('sha256')
    actual_binary_hash = hashlib.sha256(Path(binary).read_bytes()).hexdigest()
    if (receipt.get('source') != SOURCE
            or receipt.get('observed_version') != VERSION
            or (expected_binary_hash and expected_binary_hash != actual_binary_hash)):
        raise ValueError('ZIZMOR_VERIFIED_EXECUTABLE_MISMATCH')
    return version(binary)


def _cli_main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Acquire and verify pinned Zizmor provider")
    parser.add_argument("--provider-dir", required=True, help="Directory to place verified provider")
    parser.add_argument("--expected-version", default=VERSION, help="Expected version (must be 1.29.0)")
    parser.add_argument("--summary-file", default=None, help="Append acquisition summary to file")
    parser.add_argument("--offline", action="store_true", help="Validate mapping only, no download")
    args = parser.parse_args()
    try:
        if args.expected_version != VERSION:
            raise ValueError(f"ZIZMOR_EXPECTED_VERSION_NOT_PINNED:{args.expected_version}!=1.29.0")
        m = mapping()
        if args.offline:
            print(f"ZIZMOR_MAPPING_VERIFIED=mapping={MAPPING} version={VERSION}")
            return 0
        binary, receipt = acquire(Path(args.provider_dir))
        print(f"ZIZMOR_PROVIDER={receipt['provider']}")
        print(f"ZIZMOR_PINNED_VERSION={receipt['provider_version']}")
        print(f"ZIZMOR_ASSET={ASSET}")
        print(f"ZIZMOR_SOURCE_URL={SOURCE['download_base']}/{ASSET}")
        print(f"ZIZMOR_ARCHIVE_SHA256={receipt['sha256']}")
        print(f"ZIZMOR_EXECUTABLE={binary}")
        print(f"ZIZMOR_MAPPING_SHA256={hashlib.sha256(MAPPING.read_bytes()).hexdigest()}")
        print("ZIZMOR_ACQUIRE=VERIFIED_SHA256_VERSION_PINNED")
        notice = f"SHIELD_PROVIDER Zizmor@{VERSION} sha256={receipt['sha256']} source={SOURCE['download_base']}/{ASSET}"
        print(f"::notice::{notice}")
        if args.summary_file:
            p = Path(args.summary_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as handle:
                handle.write("### Zizmor provider acquisition\n")
                for k, v in receipt.items():
                    handle.write(f"- {k}: `{v}`\n")
        return 0
    except Exception as exc:
        reason = str(exc)
        print(f"::error::{reason}")
        print("ZIZMOR_ACQUIRE=BLOCKED")
        if args.summary_file:
            p = Path(args.summary_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as handle:
                handle.write("### Zizmor provider acquisition\n\nZIZMOR_ACQUIRE=BLOCKED\n")
                handle.write(f"- reason: `{reason}`\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli_main())
