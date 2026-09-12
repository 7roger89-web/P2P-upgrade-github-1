#!/usr/bin/env python3
"""Acquire and verify the pinned provider from its official release.

This is harness infrastructure for the candidate acceptance workflow: it makes
the Shield provider mapping the single source of truth for which provider
version, asset, and checksum file are allowed, and refuses to leave a usable
provider behind unless the downloaded archive matches the official checksums
entry and the extracted binary reports the pinned version.

Policy this file enforces:

- official release only (``kind == official_github_release``);
- exact pinned version only, never ``latest``, no mirror, no source build;
- sha256 of the downloaded archive must equal the official checksums entry;
- any failure is fatal for provider use and is reported as a BLOCKED cause.

Stdlib only. Exit ``0`` when a verified provider is ready, ``2`` when it is not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence

SCHEMA = "p2p-shield-provider-mapping/1"
CONTROL_ID = "SHIELD-SECRET-01"
# Slice-1 trusted provider identity: exact pin, no registry, no fallback.
EXPECTED_PROVIDER_NAME = "Gitleaks"
EXPECTED_PROVIDER_REPOSITORY = "gitleaks/gitleaks"
EXIT_READY = 0
EXIT_BLOCKED = 2
SHA256_LINE = re.compile(r"^([0-9a-f]{64})\s+\*?(?P<name>[^\s]+)\s*$")
# Standalone semver token with optional leading 'v'; word boundaries so 8.18.40
# cannot satisfy an 8.18.4 pin, and numeric suffixes are rejected.
SEMVER_TOKEN = re.compile(r"(?<!\S)v?(\d+\.\d+\.\d+)(?!\S)")
DOWNLOAD_TIMEOUT_SECONDS = 120
USER_AGENT = "p2p-shield-slice1-harness"


def _expected_download_base(repository: str, version: str) -> str:
    return f"https://github.com/{repository}/releases/download/v{version}"


def _normalize_version(output: str) -> str:
    """Return the standalone semver token from provider version output, or ''."""
    flattened = " ".join(output.split())
    match = SEMVER_TOKEN.search(flattened)
    return match.group(1) if match else ""


class ProviderAcquisitionBlocked(Exception):
    """The pinned provider cannot be made available; reason is durable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def load_and_validate_mapping(mapping_path: Path, expected_version: str) -> dict[str, Any]:
    """Return the mapping only if it still describes the pinned official provider."""
    if mapping_path.is_symlink() or not mapping_path.is_file():
        raise ProviderAcquisitionBlocked(f"MAPPING_MISSING_OR_INVALID:{mapping_path}")
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderAcquisitionBlocked(f"MAPPING_UNREADABLE:{exc}") from exc
    if not isinstance(mapping, dict):
        raise ProviderAcquisitionBlocked("MAPPING_NOT_AN_OBJECT")
    source = mapping.get("source") if isinstance(mapping.get("source"), dict) else {}
    problems = []
    if mapping.get("schema") != SCHEMA:
        problems.append(f"MAPPING_SCHEMA_UNSUPPORTED:{mapping.get('schema')}")
    if mapping.get("control_id") != CONTROL_ID:
        problems.append(f"MAPPING_CONTROL_ID_UNEXPECTED:{mapping.get('control_id')}")
    if mapping.get("provider_name") != EXPECTED_PROVIDER_NAME:
        problems.append(
            f"MAPPING_PROVIDER_NAME_UNEXPECTED:{mapping.get('provider_name')}!={EXPECTED_PROVIDER_NAME}"
        )
    if mapping.get("provider_version") != expected_version:
        problems.append(
            f"MAPPING_PROVIDER_VERSION_NOT_PINNED:{mapping.get('provider_version')}!={expected_version}"
        )
    if source.get("kind") != "official_github_release":
        problems.append(f"MAPPING_SOURCE_UNSUPPORTED:{source.get('kind')}")
    expected_repository = EXPECTED_PROVIDER_REPOSITORY
    if source.get("repository") != expected_repository:
        problems.append(
            f"MAPPING_SOURCE_REPOSITORY_UNEXPECTED:{source.get('repository')}!={expected_repository}"
        )
    if source.get("tag") != f"v{expected_version}":
        problems.append(f"MAPPING_SOURCE_TAG_UNEXPECTED:{source.get('tag')}")
    expected_base = _expected_download_base(expected_repository, expected_version)
    base_url = str(source.get("download_base", ""))
    if base_url != expected_base:
        problems.append(f"MAPPING_DOWNLOAD_BASE_UNEXPECTED:{base_url}!={expected_base}")
    if "sha256" not in str(source.get("integrity_rule", "")):
        problems.append("MAPPING_INTEGRITY_RULE_MISSING")
    if mapping.get("failure_behavior") != "BLOCKED":
        problems.append(f"MAPPING_FAILURE_BEHAVIOR_UNSUPPORTED:{mapping.get('failure_behavior')}")
    for field in ("linux_x64_asset", "checksums_asset", "extracted_binary"):
        if not str(source.get(field, "")).strip():
            problems.append(f"MAPPING_SOURCE_FIELD_MISSING:{field}")
    if problems:
        raise ProviderAcquisitionBlocked("; ".join(problems))
    mapping["_path"] = str(mapping_path)
    return mapping


def expected_checksum_from(checksums_text: str, asset_name: str) -> str:
    """Return the official sha256 entry for one asset, or refuse."""
    matches = []
    for line in checksums_text.splitlines():
        candidate = SHA256_LINE.match(line.strip())
        if candidate and candidate.group("name") == asset_name:
            matches.append(candidate.group(1))
    if not matches:
        raise ProviderAcquisitionBlocked(f"PROVIDER_CHECKSUM_ENTRY_MISSING:{asset_name}")
    if len(set(matches)) != 1:
        raise ProviderAcquisitionBlocked(f"PROVIDER_CHECKSUM_ENTRY_AMBIGUOUS:{asset_name}")
    return matches[0]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise ProviderAcquisitionBlocked(f"PROVIDER_DOWNLOAD_STATUS:{status}:{url}")
            destination.write_bytes(response.read())
    except ProviderAcquisitionBlocked:
        raise
    except (urllib.error.URLError, OSError) as exc:
        raise ProviderAcquisitionBlocked(f"PROVIDER_DOWNLOAD_FAILED:{type(exc).__name__}:{url}") from exc
    if destination.stat().st_size == 0:
        raise ProviderAcquisitionBlocked(f"PROVIDER_DOWNLOAD_EMPTY:{url}")


def extract(binary_name: str, archive: Path, provider_dir: Path) -> Path:
    staging = Path(tempfile.mkdtemp(prefix="p2p-shield-extract-", dir=str(provider_dir.parent)))
    try:
        with tarfile.open(archive, "r:gz") as handle:
            members = handle.getmembers()
            # Match by basename so a single top-level directory prefix in the
            # official archive cannot silently produce a missing provider.
            binaries = [
                member for member in members if member.isfile() and Path(member.name).name == binary_name
            ]
            if len(binaries) != 1:
                names = ",".join(member.name for member in members[:8])
                raise ProviderAcquisitionBlocked(
                    f"PROVIDER_BINARY_MEMBER_MISSING:{binary_name}:matches={len(binaries)}:members={names}"
                )
            for member in members:
                if not member.isfile():
                    continue
                source = handle.extractfile(member)
                if source is None:
                    continue
                extracted = staging / Path(member.name).name
                with extracted.open("wb") as sink:
                    sink.write(source.read())
        binary = staging / binary_name
        if not binary.is_file():
            raise ProviderAcquisitionBlocked(f"PROVIDER_BINARY_MISSING:{binary}")
        binary.chmod(0o755)
        target = provider_dir / binary_name
        os.replace(binary, target)
        return target
    finally:
        for leftover in staging.glob("*"):
            leftover.unlink(missing_ok=True)
        staging.rmdir()


def observed_version(executable: Path, timeout: int) -> str:
    try:
        process = subprocess.run(
            [str(executable), "version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProviderAcquisitionBlocked(f"PROVIDER_VERSION_COMMAND_FAILED:{type(exc).__name__}") from exc
    output = (process.stdout + process.stderr).strip()
    if process.returncode != 0:
        raise ProviderAcquisitionBlocked(
            f"PROVIDER_VERSION_COMMAND_FAILED:rc={process.returncode}:output={output[:120]}"
        )
    return output


def acquire(*, mapping_path: Path, provider_dir: Path, expected_version: str, offline: bool) -> dict[str, str]:
    mapping = load_and_validate_mapping(mapping_path, expected_version)
    source = mapping["source"]
    base_url = source["download_base"]
    archive_asset = source["linux_x64_asset"]
    checksum_asset = source["checksums_asset"]
    binary_name = source["extracted_binary"]
    provider_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "PROVIDER": mapping["provider_name"],
        "PROVIDER_PINNED_VERSION": expected_version,
        "PROVIDER_ASSET": archive_asset,
        "PROVIDER_SOURCE_URL": f"{base_url}/{archive_asset}",
        "PROVIDER_MAPPING_SHA256": sha256_of(mapping_path),
    }
    if offline:
        summary["PROVIDER_ACQUIRE"] = "OFFLINE_CHECK_ONLY"
        return summary
    checksums_path = provider_dir / checksum_asset
    archive_path = provider_dir / archive_asset
    download(f"{base_url}/{checksum_asset}", checksums_path)
    download(f"{base_url}/{archive_asset}", archive_path)
    expected = expected_checksum_from(checksums_path.read_text(encoding="utf-8"), archive_asset)
    actual = sha256_of(archive_path)
    summary["PROVIDER_ARCHIVE_SHA256"] = actual
    if actual != expected:
        archive_path.unlink(missing_ok=True)
        raise ProviderAcquisitionBlocked(
            f"PROVIDER_CHECKSUM_MISMATCH:official={expected}:actual={actual}"
        )
    executable = extract(binary_name, archive_path, provider_dir)
    observed_raw = observed_version(executable, DOWNLOAD_TIMEOUT_SECONDS)
    observed = _normalize_version(observed_raw)
    if observed != expected_version:
        executable.unlink(missing_ok=True)
        raise ProviderAcquisitionBlocked(
            f"PROVIDER_VERSION_MISMATCH:pinned={expected_version}:observed={observed_raw[:120]}"
        )
    summary["PROVIDER_ACQUIRE"] = "VERIFIED_SHA256_VERSION_PINNED"
    summary["PROVIDER_EXECUTABLE"] = str(executable)
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--mapping",
        required=True,
        help="Shield provider mapping file that declares the allowed provider",
    )
    parser.add_argument("--provider-dir", required=True, help="Directory to place the verified provider in")
    parser.add_argument(
        "--expected-version",
        default="8.18.4",
        help="Provider version this slice is allowed to use; a different mapping is refused",
    )
    parser.add_argument(
        "--summary-file",
        default=None,
        help="Append the acquisition result to this file (for example GITHUB_STEP_SUMMARY)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Validate the mapping policy only; do not download or run anything",
    )
    return parser.parse_args(argv)


def _write_summary(path: str | None, lines: Sequence[str]) -> None:
    if not path:
        return
    summary_path = Path(path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = acquire(
            mapping_path=Path(args.mapping),
            provider_dir=Path(args.provider_dir),
            expected_version=args.expected_version,
            offline=args.offline,
        )
    except ProviderAcquisitionBlocked as exc:
        lines = exc.reason.split("; ")
        for line in lines:
            print(f"::error::{line}")
        print("PROVIDER_ACQUIRE=BLOCKED")
        _write_summary(
            args.summary_file,
            ["### Provider acquisition", "", "PROVIDER_ACQUIRE=BLOCKED", ""]
            + ["- %s" % line for line in lines],
        )
        return EXIT_BLOCKED
    for key, value in summary.items():
        print(f"{key}={value}")
    if not args.offline:
        print(
            "::notice::SHIELD_PROVIDER %s@%s sha256=%s source=%s"
            % (
                summary["PROVIDER"],
                summary["PROVIDER_PINNED_VERSION"],
                summary.get("PROVIDER_ARCHIVE_SHA256", "UNVERIFIED"),
                summary["PROVIDER_SOURCE_URL"],
            )
        )
    _write_summary(
        args.summary_file,
        ["### Provider acquisition", ""] + ["%s: `%s`" % (key, value) for key, value in summary.items()],
    )
    return EXIT_READY


if __name__ == "__main__":
    raise SystemExit(main())
