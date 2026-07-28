# Security Policy

## Supported versions

Security fixes are applied to the default branch (`main` / active development branches). Older tags may not receive patches.

## Reporting a vulnerability

**Do not** open public GitHub issues for security-sensitive reports.

1. Contact LG AI Research / the repository maintainers via the project’s private security channel, or open a **private** security advisory if enabled on the host. Do not rely on [`LICENSE.md`](LICENSE.md) for contact details (it is the license text only).
2. Include: impact, reproduction steps, affected paths, and suggested fix if any.
3. Allow reasonable time for triage before public disclosure.

## Secrets

- Never commit `.env`, API keys, or tokens.
- Redact `EXAONE_API_KEY` in logs, issues, and notebook outputs (`eval/reports/` is gitignored for this reason).
- Rotate keys immediately if exposed.

## External services

Notebooks and `implementations/` demos may call third-party HTTP APIs (Context7, DuckDuckGo, Hugging Face, etc.). Use allowlists and rate limits in production; recipe code is for **learning**, not unauthenticated public deployment.
