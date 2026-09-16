"""Thin CLI for exporting a verified project experience promotion proposal.

Project executors may build a proposal, but they do not mutate the canonical
P2P shared catalog or P2P main. Control Tower/canonical P2P validates and
applies promotable DOMAIN/CROSS_PROJECT proposals separately.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .experience_evolution import ExperienceEvolutionError
from .experience_federation import ExperienceFederationError, build_promotion_proposal

SCHEMA = "p2p-experience-promotion-cli/1"


def _read_spec(path: str | Path) -> Mapping[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperienceFederationError("PROMOTION_SPEC_INVALID") from exc
    if not isinstance(value, Mapping):
        raise ExperienceFederationError("PROMOTION_SPEC_OBJECT_REQUIRED")
    return value


def build_from_spec(root: str | Path, experience_id: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    source_project = str(spec.get("source_project") or "").strip()
    if not source_project:
        raise ExperienceFederationError("SOURCE_PROJECT_REQUIRED")
    return build_promotion_proposal(
        root,
        experience_id,
        source_project=source_project,
        scope=str(spec.get("scope") or "PROJECT_ONLY"),
        domain=str(spec.get("domain") or ""),
        scope_evidence=spec.get("scope_evidence") or (),
        procedure=spec.get("procedure") or (),
        inputs=spec.get("inputs") or (),
        outputs=spec.get("outputs") or (),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--experience-id", required=True)
    parser.add_argument("--spec-file", required=True)
    args = parser.parse_args(argv)
    try:
        proposal = build_from_spec(args.root, args.experience_id, _read_spec(args.spec_file))
    except (ExperienceFederationError, ExperienceEvolutionError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"schema": SCHEMA, "status": "PASS", "proposal": proposal}, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
