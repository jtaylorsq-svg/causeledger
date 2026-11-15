# Architecture and MVP boundary

## Product decision

The smallest useful product is one complete investigation that a facilitator can run, inspect and export without buying or deploying an ERP. The target audience is manufacturing quality and continuous-improvement practitioners. Version 0.1 is a personal facilitator's workbench; collaborative team hosting is deliberately not implemented.

The specific value proposition is an explicit, testable evidence chain rather than a generic task list. This is a design hypothesis, not a verified claim of market uniqueness.

## Components

| Component | Responsibility |
| --- | --- |
| `domain.py` | Pure commands, validation, closure readiness and evidence dependency rules |
| `store.py` | SQLite transaction boundary, case revisions, event snapshots and hash chain |
| `server.py` | Loopback HTTP adapter, route allowlist, Host/Origin/body restrictions |
| `static/` | Framework-free UI, escaped rendering, same-origin requests |
| `demo.py` | Fictional examples generated through the same commands as ordinary records |
| `verify.py` | Offline export chain and latest-snapshot consistency checks |
| `tests/` | Domain, persistence, invalidation and HTTP security regression tests |

## Aggregate and traceability

A case owns containment records, evidence, causes and actions. UUID identifiers are scoped through case lookup. Commands cannot link evidence or causes from another case. Every accepted write increments the case revision and appends an event containing actor, timestamp, command, resulting snapshot and a hash incorporating the previous event hash. The event chain spans the installation, preserving interleaved case writes.

Writes use `BEGIN IMMEDIATE`. The incoming revision must match before the command is applied. A failure rolls back both the case and its event. Export reads cases and events in one transaction. Browser save errors retain the entered form. A stale version requires reload and human review.

## Commands

Create case; correct case facts; record/review evidence; define/confirm/dispose containment; propose/verify cause; plan/implement action; record effectiveness; close; reopen.

The UI is an adapter. Server/domain rules enforce the gates even if the UI is bypassed. Unknown commands fail. Owners and dates are required at case, containment and action planning; human verification records carry actor attribution in the event.

## Closure policy v1

- Every containment record has population boundaries, physical identification, owner/date, accepted execution proof, disposition text and accepted disposition proof.
- Both occurrence and escape have a verified cause, mechanism, verification method, result and accepted proof.
- Every proposed cause is verified and has a corrective action. v0.1 lacks a ruled-out hypothesis state; this is a known usability limitation with a tracked roadmap item.
- Every action links a verified cause and has implementation proof plus an explicit passing effectiveness result, accepted proof and ordered, completed observation dates.
- Effectiveness metric, target and required sample/window are set at planning. The human reviewer compares measured results against them. Software does not parse free text or certify the comparison.
- Evidence withdrawal/rejection recalculates readiness. Changed cause verification invalidates dependent implementation/effectiveness; reimplementation clears prior effectiveness.
- Closed cases are immutable until explicitly reopened with a reason. Earlier snapshots remain available. No silent override of missing proof is provided.

## Deliberate exclusions

No email ingestion, AI inference, employer-specific 8D template, customer integration, document attachment storage, notifications, ERP, analytics, organizational master data, SSO, shared team editing or compliance claim. Case facts can be corrected; detailed action editing and retired hypotheses need explicit invalidation policies before implementation.

## Security and operational limits

The stdlib HTTP server is for local evaluation, not a production-facing web service. SQLite backups require stopping the service in v0.1. JSON is an inspectable export, not a supported restore protocol. All identities are self-reported. A privileged user can change the database and rebuild the hash chain. See SECURITY.md.

## Architecture decisions

1. Fresh Python implementation with standard-library-only runtime: easy local evaluation, inspectable rules and small dependency surface.
2. Pure domain module: easier testing and future replacement of HTTP/storage adapters.
3. Local SQLite instead of cloud storage: no credentials, hidden data transmission or premature team-hosting promises.
4. Required human evidence review: automation derives gaps; it does not manufacture verification.
5. No source copied from a private reference prototype: public artifact has independent code, assets, fictional fixtures and Git history.
