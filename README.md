# CauseLedger

**Close corrective actions with evidence.**

A small, self-hosted corrective-action workbench for manufacturing investigations. Keep the problem, containment, occurrence and escape causes, corrective actions, and effectiveness records in one traceable case.

**Status: v0.1 release candidate.** This is a new project with no claimed external adoption. It currently supports one operator on localhost, not shared team access. Automated workflow and HTTP tests pass; interactive browser QA and public release remain pending.

## Why it exists

Completing a task does not establish a cause or demonstrate that an action worked. CauseLedger makes missing proof visible and blocks closure while required records are missing or invalidated.

Evidence → Failure Mechanism → Verified Cause → Corrective Action → Effectiveness

The application records human review decisions. It does not independently establish physical truth, approve product release, certify compliance, or replace engineering judgment.

## Try it

Python 3.11 or later. No runtime third-party packages, account, API key, build step or cloud service required.

```sh
python3 -m causeledger.server --demo
```

Open **http://127.0.0.1:8765**. On Windows, use `py -3` if `python3` is unavailable. The demo seeds only an empty database. All demo records are explicitly fictional.

To start empty:

```sh
python3 -m causeledger.server --db data/my-investigations.sqlite3
```

For isolated evaluation, choose a separate database path. Demo data is never silently added to an existing investigation database. Stop with Ctrl+C.

## What v0.1 does

- Defines a problem, accountable case owner and due date.
- Records suspect population boundaries, physical hold identification, execution proof, and containment disposition proof.
- Keeps reported evidence separate from accepted, rejected and withdrawn evidence, with reviewer rationale.
- Separates occurrence causes from escape causes and records each failure mechanism and verification test.
- Links actions to verified causes, distinguishes prevention from detection, and requires an owner, due date, deliverable, metric, target and observation window.
- Requires implementation evidence and a passing, dated effectiveness result for every action before closure.
- Recalculates gaps after evidence withdrawal. Reverification of a cause invalidates downstream implementation and effectiveness records.
- Preserves revisions in SQLite transactions and detects stale updates instead of silently overwriting them.
- Exports JSON with event history; checks export consistency using a hash chain.

## A five-minute walkthrough

1. Select **DEMO · Washer omitted at assembly**.
2. Inspect its two cause paths and linked prevention/detection actions.
3. See the one remaining gap: escape-action effectiveness has not been demonstrated.
4. Choose **Close case**, enter a recorder and reason, and save. Closure is blocked.
5. Use the [demo guide](docs/DEMO.md) to record the missing fictional result, close, reopen and withdraw proof.

[Visual demo storyboard](docs/demo-storyboard.svg) · [Architecture](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md)

The storyboard illustrates the fictional example. It is not an application screenshot. Browser screenshots will be added after the browser QA release gate passes.

## Storage and security

Data stays in the SQLite file specified by `--db`. The service binds only to `127.0.0.1`, checks Host and Origin, and does not enable cross-origin access. No telemetry or external requests are included.

One operator controls the installation. Names are self-reported, not authenticated identities. SQLite event-update/delete triggers and the export hash chain help reveal accidental inconsistency; a database administrator can bypass them or recompute the chain. This is not a tamper-proof or regulated electronic-record system.

Do not expose this HTTP service through a public tunnel, reverse proxy, container port mapping or shared network. Shared team deployment requires the authentication and authorization work on the roadmap. See [SECURITY.md](SECURITY.md).

**Back up:** stop the service, then copy the SQLite database to a protected location. Restore by stopping the service and running with that backup path. JSON export is portable inspection data, not yet an import/restore format. Evidence consists of text observations and source references; attached source files are not retained in v0.1.

## Develop and validate

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q causeledger
node --check causeledger/static/app.js
node --test tests/js/*.test.cjs
python3 scripts/privacy_check.py
```

Node is optional for running the application; it is used here only for JavaScript syntax checks. CI is configured for Python 3.11, 3.12 and 3.13. Configured CI is not a claim that remote CI has run.

Check an exported JSON record:

```sh
python3 -m causeledger.verify causeledger-export.json
```

See the [latest local requalification report](docs/QA-2026-11-15.md) for tested stages and remaining release gates.

## Contribute

Start with the acceptance criteria in [CONTRIBUTING.md](CONTRIBUTING.md). Reproducible rule failures and clear shop-floor examples are more useful than feature volume. Use fictional data in issues, tests and screenshots. Never upload employer, customer, employee or production information.

The initial implementation was created with AI coding assistance and reviewed through automated checks. Human field validation and independent code review remain important next steps. There are no claims of users, customers, stars, downloads or production deployments.

MIT licensed. See [LICENSE](LICENSE).
