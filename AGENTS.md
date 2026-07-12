# SignalForge repository instructions

## Source of truth

- Read `specs/README.md` before specification or implementation work.
- Treat approved documents in `specs/` as the source of truth. Files in `docs/project-context/` are background only.
- Do not implement observable behavior absent from an approved feature specification.
- Never assign `Approved` yourself. Only a human may approve a specification.

## Required SDD workflow

1. Create or update the product specification.
2. Create a feature specification in `Draft`.
3. Review it and move it to `In Review` when ready.
4. Stop for explicit human approval.
5. Create the technical design.
6. Decompose the design into tasks.
7. Implement one explicitly selected task.
8. Verify that task and update its checkbox only after its criteria pass.
9. Verify the complete feature against its acceptance criteria.
10. Record significant decisions and update lifecycle statuses.

Do not advance to the next stage or task without explicit user direction.

## Implementation rules

- Before implementing, read the feature's `spec.md`, `design.md`, `tasks.md`, and relevant decisions.
- Keep changes within the selected task's scope.
- Add or update relevant tests and run all applicable checks.
- Record significant technical decisions in the feature's `decisions.md`.
- Validation commands are `TBD` until the approved technical design selects a stack. A design must define applicable test, lint, type-check, and security checks before implementation begins.

## Security

- Never read or print `.env`, credentials, Telegram sessions, or other secrets.
- Never commit `.env`, `*.session`, or `*.session-journal` files.
- Do not place real secrets or session data in examples, fixtures, logs, or documentation.
- Do not access external services unless the user explicitly requests it.

## Lightweight changes

Typo, formatting, non-behavioral documentation, and maintenance-only changes do not require the full SDD cycle. Any observable behavior change does.
