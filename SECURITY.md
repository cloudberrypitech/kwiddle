# Security Policy

## Supported Versions

Security updates are provided for actively maintained releases of Kwiddle.

| Version                           | Supported      |
| --------------------------------- | -------------- |
| Latest release                    | ✅              |
| Older releases                    | ⚠️ Best effort |
| Unreleased / development versions | ❌              |

Users are encouraged to use the latest available version of Kwiddle when possible.

## Reporting a Vulnerability

If you discover a security vulnerability in Kwiddle, please **do not report it through a public GitHub issue**.

Instead, use GitHub's **private vulnerability reporting** feature for this repository, if available:

**GitHub → Security → Advisories → Report a vulnerability**

Private vulnerability reports allow the maintainers to investigate and discuss the issue without publicly exposing details before a fix is available.

If private vulnerability reporting is unavailable, please contact the Kwiddle maintainers privately through the contact information listed in the repository or organization profile.

When reporting a vulnerability, please include as much of the following information as possible:

* A clear description of the vulnerability.
* The affected Kwiddle version or commit.
* The affected operating system and environment.
* Steps required to reproduce the issue.
* A minimal proof of concept, if applicable.
* The potential security impact.
* Any suggested mitigation or fix, if known.

Please avoid including passwords, private keys, access tokens, personal information, or other sensitive data in a report.

## Response Timeline

We aim to:

* Acknowledge a security report within **7 days**.
* Investigate and assess the reported issue as soon as reasonably possible.
* Keep the reporter informed when significant progress is made.
* Release a fix or mitigation when practical and appropriate.
* Coordinate public disclosure with the reporter when the vulnerability has been confirmed.

These are target timelines rather than guarantees. Response times may vary depending on the complexity and severity of the issue.

## Responsible Disclosure

Please allow the maintainers reasonable time to investigate and address a reported vulnerability before publicly disclosing technical details.

Security researchers are asked to:

* Avoid accessing, modifying, deleting, or exposing data that does not belong to them.
* Avoid disrupting services or systems used by other users.
* Avoid testing against other people's devices, accounts, or data.
* Avoid intentionally degrading the availability or performance of Kwiddle or related infrastructure.
* Stop testing if you encounter sensitive information that is not necessary to demonstrate the vulnerability.
* Keep vulnerability details private until an appropriate disclosure date has been agreed upon.

Good-faith security research is appreciated, and we will make reasonable efforts to work with researchers to understand and resolve legitimate vulnerabilities.

## Scope

This policy applies to security vulnerabilities in the Kwiddle source code and officially distributed Kwiddle software.

Third-party dependencies, operating systems, hardware, external services, and unrelated projects may be outside the direct control of the Kwiddle maintainers. Reports involving such components are still welcome when they materially affect Kwiddle, but they may need to be coordinated with the relevant upstream project.

## Security Updates

When appropriate, confirmed security vulnerabilities may result in:

* A patched release.
* A security advisory.
* Updated documentation or mitigation guidance.
* A CVE or other vulnerability identifier, where appropriate and available.

Public disclosure will generally occur after a fix or reasonable mitigation is available.

## Thank You

We appreciate responsible security research and the effort of researchers who help make Kwiddle safer for everyone.
