# Contributing

CauseLedger is early software. Small changes with objective evidence are welcome. The maintainer decides scope; no response-time promise is implied.

## Start with a real problem

For bugs, include expected behavior, observed behavior, version, reproduction steps and a fictional minimal case. For proposals, describe the manufacturing decision the change improves and its acceptance criteria. Do not post private production data or credentials. Follow SECURITY.md for vulnerabilities.

## Local workflow

1. Create a branch for one concern.
2. Run `python3 -m causeledger.server --demo --db data/contributor-demo.sqlite3`.
3. Change domain rules in `causeledger/domain.py`; keep organization-specific procedures out.
4. Add regression tests for changed invariants. Run `python3 -m unittest discover -s tests -v`, Python compilation, JavaScript syntax checking and `python3 scripts/privacy_check.py`.
5. For UI changes, verify creation, save, reload, invalid commands, closure blocking and export at desktop and phone widths. Include screenshots containing fictional data only.
6. Open a pull request explaining the problem, resulting behavior, validation and limitations.

## Invariants

- A hypothesis is never silently promoted to a verified cause.
- Reported completion is not accepted proof.
- Occurrence and escape causes remain separate.
- Detection is never labeled prevention.
- Actions retain a cause link, owner, due date, deliverable and effectiveness plan.
- Changes are transactional, versioned and inspectable; stale saves fail.
- Closure gaps are derived from current evidence, not stored checkbox summaries.
- No automatic LLM judgment of cause validity or effectiveness.

## Review standards

Keep dependencies small. Explain schema migrations and backup behavior. Include a failure-path test when changing gates. Do not claim standard compliance or security guarantees that have not been validated. Disclose AI assistance when relevant and review its output as ordinary untrusted code.

Contributions are offered under the project's MIT license. No contributor license agreement is currently required.

## Conduct

Be respectful, practical and specific. Challenge evidence and designs without attacking people. Maintainers may remove harassment, confidential information or spam. There is no fabricated team, advisory board or support organization behind this project.
