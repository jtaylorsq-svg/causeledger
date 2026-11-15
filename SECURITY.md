# Security

## Supported scope

Only the current v0.1 candidate is maintained. There is no long-term support commitment yet.

This release is a **single-operator, loopback-only workbench**. It has no authentication, roles, electronic signatures, encryption at rest or multi-tenant isolation. An actor name is a self-reported attribution field. It is not a verified user identity.

Do not deploy it on the internet or an untrusted shared host. Do not bypass its loopback, Host or Origin restrictions. Protect the machine, SQLite file, backups and JSON exports using operating-system controls. All authorized local users/processes should be considered within the trust boundary.

## Implemented protections

- Loopback-only binding with exact Host checks against DNS rebinding.
- Same-origin POST checks, JSON-only writes and a 64 KiB request-body limit.
- Parameterized SQL, allowlisted static assets, no arbitrary file retrieval.
- Escaped user content and a restrictive Content Security Policy.
- Transactional writes and optimistic concurrency checks.
- Append-only event triggers and export consistency checking.

These are implementation properties, not the result of an independent penetration test. Hash chains have no external trust anchor. A privileged person can alter SQLite or recompute hashes. Evidence references do not preserve the referenced file's content or authenticity.

## Report a vulnerability

After public publication, use the repository's **Security → Report a vulnerability** private advisory flow if enabled. Do not post exploit details, private case data or secrets in a public issue. If private reporting is unavailable, open a minimal issue requesting a private reporting channel without disclosing the vulnerability. The maintainer must enable private vulnerability reporting as part of publication.

No response SLA, bug bounty or security-team capacity is promised.
