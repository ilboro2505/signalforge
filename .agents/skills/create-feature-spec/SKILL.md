---
name: create-feature-spec
description: Create or materially revise a SignalForge feature specification. Use when the user asks to define a new feature, turn requirements into a feature spec, or change feature scope, requirements, constraints, or acceptance criteria.
---

# Create feature specification

1. Read `AGENTS.md`, `specs/README.md`, the approved product specification, relevant architecture documents, and `specs/templates/feature-spec-template.md`.
2. Confirm the feature does not duplicate an existing feature and choose the next available numeric directory ID.
3. Separate observable requirements from implementation choices. Use stable `REQ-NNN` and `AC-NNN` identifiers local to the feature.
4. State in-scope and out-of-scope behavior, constraints, edge cases, dependencies, and unresolved questions.
5. Create or update `spec.md`. Set a new or materially changed specification to `Draft`; clear stale approval metadata.
6. Do not create a design, tasks, or implementation. Do not set `Approved`.
7. Report assumptions, unresolved questions, and the review needed next.

Stop when missing product decisions would materially change the specification.
