# Historical local validation record

For the current source-publication and GitHub CI evidence, see [2026-11-15 requalification](QA-2026-11-15.md). The table below records the original candidate checks, not the present repository state.

Date: 2026-10-25. Candidate: 0.1.0rc1. Runtime: Python 3.12.14.

| Check | Actual result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 32 tests passed |
| Python compilation | Passed |
| JavaScript syntax (`node --check`) | Passed using Node 24.22.1 |
| Release hygiene patterns | Passed; limited patterns, not comprehensive leak/security certification |
| Wheel build | Passed, no runtime third-party dependencies |
| Install into fresh virtual environment without package-index access | Passed |
| Installed package smoke | HTML, JS, CSS and case API served; fictional seed and export integrity checker passed |
| Demo storyboard visual inspection | Passed; explicitly illustrative, not an application screenshot |
| Interactive browser QA | BLOCKED: available cloud browser returned connection refused for local app server |
| Remote GitHub CI | Not run: separate repository not created |
| Python 3.11 / 3.13 execution | Configured in CI, not run locally |
| Independent security review | Not performed |
| External user evaluation / adoption | No evidence available |

The automated suite covers closed-case mutation blocking, closure completeness, occurrence/escape separation, all-containment disposition, action proof, failed effectiveness, invalid observation dates, stale revisions, cross-case references, rollback, persistence, append-only event triggers, reimplementation/cause invalidation, export-chain tampering, Host/Origin restrictions, JSON content type, size limits and static path allowlisting.

This record does not substitute for the outstanding browser gate. No final v0.1.0 release is claimed.
