# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x (pre-release) | ✅ |

## Reporting a Vulnerability

**Do not report security vulnerabilities via public GitHub issues.**

Please report security vulnerabilities by emailing **security@capsule.dev** with:

- A description of the vulnerability
- Steps to reproduce the issue
- The potential impact
- Any suggested mitigations (optional)

You will receive an acknowledgment within **48 hours** and a detailed response within **7 days** indicating next steps.

## Disclosure Policy

- We will acknowledge receipt of your report within 48 hours
- We will confirm the vulnerability and assess its severity within 7 days
- We will release a patch as soon as possible depending on severity:
  - **Critical (P0):** Within 24 hours
  - **High (P1):** Within 7 days
  - **Medium (P2):** Within 30 days
  - **Low (P3):** Within 90 days
- We will publicly disclose the vulnerability after a patch is released, with credit to the reporter (unless you prefer to remain anonymous)

## Scope

The following are in scope for security reports:

- The `capsule-sdk` Python package
- The Capsule Cloud API (`api.capsule.dev`)
- The Capsule Cloud web dashboard
- Authentication and authorization bypasses
- Data isolation failures between workspaces
- Cryptographic weaknesses in the `.capsule` file format

The following are out of scope:

- Vulnerabilities in third-party dependencies (report directly to them)
- Denial of service attacks requiring significant resources
- Social engineering attacks
- Physical attacks on infrastructure

## Security Design Principles

Capsule is built with security-by-default:

- All data encrypted at rest (AES-256) and in transit (TLS 1.3)
- API keys stored as Argon2id hashes (never in plaintext)
- JWT tokens use EdDSA (Ed25519) — never HS256
- Row-Level Security (RLS) enforced at the database for all multi-tenant data
- Each replay runs in an isolated Modal sandbox with no shared state
- PII redaction available at capture time via configurable rules

## Bug Bounty

A formal bug bounty program will launch at Phase 4. Until then, we will acknowledge all valid reports and list researchers in our Hall of Fame.
