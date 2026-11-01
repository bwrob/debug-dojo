# Security Policy

This policy explains which project versions receive security fixes and how to report a
vulnerability.

## Supported Versions

Only the latest release of **Debug Dojo** receives active security
updates and vulnerability patches.

| Version                        | Supported          |
| :----------------------------- | :----------------- |
| `0.9.0.x` | :white_check_mark: |
| `< 0.9.0` | :x:                |

We officially support and test against Python `3.12` and
later.

## Reporting a Vulnerability

The **Debug Dojo** team takes the security of our software
seriously. If you believe you have discovered a vulnerability, please report it
responsibly:

> [!CAUTION]
> **Do not report security vulnerabilities through public GitHub issues or
> discussions.**

### Preferred Reporting Method

1. **GitHub Private Vulnerability Reporting**:
   - Navigate to the repository's **Security** tab on GitHub.
   - Click on **Advisories** and select **Report a vulnerability**.
   - Provide a detailed summary, proof of concept (PoC), and impact assessment.

2. **Direct Security Contact**:
   - If GitHub Private Reporting is unavailable, send an email to
     **bwrob** at [bartosz.marcin.wroblewski@gmail.com](mailto:bartosz.marcin.wroblewski@gmail.com) with the subject line
     `[SECURITY] Debug Dojo Vulnerability Report`.
   - Please include reproduction steps, affected environment/versions, and any proposed
     mitigation.

## Vulnerability Handling & Response Timeline

When a report is received:

1. **Acknowledgment**: We acknowledge receipt of the report within **48 hours**.
2. **Assessment & Triage**: We assess the severity, verify the proof-of-concept, and
   determine the blast radius within **5 business days**.
3. **Patch Development**: We develop and validate a remediating patch in a private
   repository fork.
4. **Coordinated Disclosure**: We publish a security release on PyPI, notify affected
   parties, and publish a GitHub Security Advisory (GHSA).

## Supply Chain Security Practices

To safeguard downstream consumers, this repository enforces:

- **Hermetic Builds**: Dependencies are resolved strictly via `uv.lock`.
- **Zero-Day Supply Chain Buffer**: Automated `exclude-newer` cutoffs buffer against
  recently published upstream package compromise.
- **Workflow Auditing**: GitHub Actions workflows are statically scanned against
  vulnerability patterns with `zizmor`.
- **Build Provenance**: Released wheels and source archives include cryptographic build
  provenance attestations (PEP 740) signed via Sigstore OIDC.
