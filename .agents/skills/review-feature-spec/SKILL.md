---
name: review-feature-spec
description: Review a SignalForge feature specification for readiness, clarity, consistency, traceability, and testability. Use when the user asks to review, critique, validate, or prepare a draft feature specification for approval.
---

# Review feature specification

1. Read `AGENTS.md`, `specs/README.md`, the feature `spec.md`, the product specification, and relevant architecture documents.
2. Check product alignment, scope boundaries, unambiguous observable requirements, measurable acceptance criteria, failure behavior, constraints, dependencies, and one-to-one traceability gaps between `REQ` and `AC` identifiers.
3. List findings by severity with exact document references. Distinguish blockers from non-blocking suggestions.
4. Do not silently resolve product ambiguity or edit implementation code.
5. If asked to apply corrections, keep the status `Draft` while materially changing requirements. If no blockers remain and the user asked to prepare it for approval, set `In Review`.
6. Never set `Approved`; request explicit human approval as the next step.
