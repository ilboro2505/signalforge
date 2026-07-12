---
name: implement-spec-task
description: Implement one explicitly selected SignalForge task from an approved feature. Use when the user names a TASK identifier or clearly selects one task for implementation under the repository's SDD workflow.
---

# Implement one specification task

1. Read `AGENTS.md`, `specs/README.md`, and the feature's `spec.md`, `design.md`, `tasks.md`, and relevant entries in `decisions.md`.
2. Confirm the specification is `Approved`, the task is explicitly selected and unchecked, dependencies are complete, and verification commands are defined. Stop on contradiction or missing approval.
3. Inspect the working tree and preserve unrelated user changes.
4. Implement only the selected task. Add or update its relevant tests and documentation.
5. Run the task's verification plus applicable project checks. Diagnose failures; do not weaken tests or requirements to obtain a pass.
6. Record significant decisions. Check the task only after its scope, criteria, and checks all pass.
7. Report changed files, verification evidence, remaining risks, and the task status. Do not begin another task.
