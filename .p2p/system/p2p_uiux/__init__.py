"""Reusable, offline-safe P2P UI/UX capability."""

__version__ = "8.4.7-C-codex.24"

from .accessibility import audit_design_system
from .contracts import contract_requirements, generate_contract, validate_contract
from .design_system import generate_design_system, load_design_system, write_design_system
from .drift import compare_design_systems
from .governance import load_manifest, validate_manifest, validate_quorum
from .recommendation import build_recommendation
from .router import classify_request, foundation_route
from .design_intelligence import (
    build_obligation_plan,
    build_task_profile,
    classify_materiality,
    correction_loop,
    design_intelligence_route,
    evaluate_completion,
    load_registry,
    route_design_task,
    validate_registry,
    validate_task_profile,
)

__all__ = [
    "audit_design_system",
    "build_recommendation",
    "classify_request",
    "foundation_route",
    "compare_design_systems",
    "contract_requirements",
    "generate_contract",
    "generate_design_system",
    "load_design_system",
    "load_manifest",
    "validate_contract",
    "validate_manifest",
    "validate_quorum",
    "write_design_system",
    "build_obligation_plan",
    "build_task_profile",
    "classify_materiality",
    "correction_loop",
    "design_intelligence_route",
    "evaluate_completion",
    "load_registry",
    "route_design_task",
    "validate_registry",
    "validate_task_profile",
]
