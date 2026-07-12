---
name: verify-spec
description: Verify a SignalForge task or complete feature implementation against its approved specification without automatically fixing it. Use when the user asks to verify acceptance criteria, audit spec compliance, or decide whether a task or feature is complete.
---

# Verify specification compliance

1. Read `AGENTS.md`, `specs/README.md`, and the feature's approved `spec.md`, `design.md`, `tasks.md`, decisions, implementation, and tests.
2. Choose the requested level: selected task or complete feature. For feature verification, require all tasks to be complete.
3. Build a traceability check from every applicable `REQ` and `AC` to implementation and test evidence.
4. Run all verification commands defined by the design. Inspect security, failure behavior, scope creep, and regressions.
5. Report findings by severity with file references and command results. Do not modify code during verification unless the user separately asks for fixes.
6. Mark a task complete only when its criteria pass. Set a feature to `Verified` only when all acceptance criteria and required checks pass; otherwise leave its status unchanged.
7. Never set `Approved`.
