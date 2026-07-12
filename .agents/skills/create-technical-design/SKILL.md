---
name: create-technical-design
description: Create or revise a SignalForge technical design for an approved feature specification. Use when the user asks how an approved feature should be implemented or requests its design document.
---

# Create technical design

1. Read `AGENTS.md`, `specs/README.md`, the feature's approved `spec.md`, relevant architecture documents and decisions, and `specs/templates/design-template.md`.
2. Stop if the feature is not `Approved`, approval metadata is absent, or requirements materially conflict.
3. Design only behavior required by the specification. Define responsibilities, interfaces, data flow, data changes, error handling, observability, security, and migration impact.
4. Define concrete applicable test, lint, type-check, and security commands before implementation can begin.
5. Map design elements to requirement and acceptance-criterion IDs. Document meaningful alternatives and risks.
6. Update `design.md` and record accepted significant decisions in `decisions.md` when directed.
7. Do not decompose tasks or implement code unless the user separately requests the next SDD stage.
