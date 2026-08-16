# P2P Optional Project Domain Model Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Purpose

Offer a lightweight, optional project-domain vocabulary artifact so reusable capabilities can understand a project without hardcoding games, logistics, SaaS, or any other domain into core governance.

## Artifact boundary

The model may describe project name, domain label, user/persona vocabulary, workflows, constraints, stack hints, sensitivity, and provenance. It is project context, not P2P authority. It is not required for trivial tasks and is never generated into a real project by this foundation Goal.

## Use and scope

The router may use the model to resolve relevant context and negative triggers. A capability may consume only fields within its declared scope. The model cannot add an agent, change the quorum, grant permissions, approve Design System or fact changes, or instruct a provider.

## Freshness and conflict

Domain entries have provenance and freshness. Stale, ambiguous, or conflicting vocabulary is reported rather than silently merged. Owner-provided product terminology can clarify project context within the existing approval boundary; it cannot override canonical governance.

## Security and lifecycle

The model is filtered for sensitivity and project scope. It is never treated as executable instruction. Tests use temporary project roots and synthetic vocabulary only. A later project-install Goal may decide whether and how to persist it; this Goal defines no installer migration.

## Done when

The foundation can optionally carry project-specific vocabulary through context pointers without hardcoded domain logic, authority escalation, or mandatory ceremony for small work.
