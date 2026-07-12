---
name: decompose-feature-tasks
description: Decompose an approved SignalForge feature specification and completed technical design into small verifiable implementation tasks. Use when the user asks for a task plan, implementation breakdown, or tasks.md for a feature.
---

# Decompose feature tasks

1. Read `AGENTS.md`, `specs/README.md`, the approved `spec.md`, completed `design.md`, relevant decisions, and `specs/templates/tasks-template.md`.
2. Stop if the specification is not approved, the design has unresolved implementation blockers, or verification commands are undefined.
3. Create ordered, independently verifiable tasks with local `TASK-NNN` IDs. Map every task to requirements or acceptance criteria and state dependencies and verification.
4. Keep each task small enough for one focused implementation cycle. Include tests and documentation in the task that changes the behavior they cover.
5. Ensure the complete task set covers the design without adding scope.
6. Leave every new checkbox unchecked. Do not implement a task or automatically select the next one.
