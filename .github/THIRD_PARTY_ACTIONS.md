# Third-Party GitHub Actions Security Documentation

This document tracks third-party GitHub Actions used in this repository and their security vetting status, in accordance with [Deltares GitHub FAQ guidelines](https://publicwiki.deltares.nl/spaces/GIT/pages/279642305/GitHub#Pages-FAQ).

**Definition**: Third-party actions are automation Actions created by anyone other than Deltares or GitHub.

---

## Approved Actions

### SonarSource/sonarqube-scan-action

**Current Version:** v6.0.0
**Commit SHA:** `fd88b7d7ccbaefd23d8f36f73b59db7a3d246602`
**Vetted Date:** 2025-01-15
**Vetted By:** [Your team/name]

**Purpose:** Integrates continuous code quality and security analysis with SonarQube directly into GitHub Actions workflows

**Security Assessment:**
- [✓] **Verified Organization:** SonarSource is a GitHub verified organization (domains: sonarsource.com, www.sonarsource.com)
- [✓] **Repository Owner Trust:** High - Established company from Switzerland, creator of popular SonarQube tool (10k+ stars)
- [✓] **Well-Maintained:** Active development with 125+ commits
- [✓] **Community Trust:** 318 stars, 160 forks
- [✓] **On Deltares Allowlist:** `SonarSource/sonarqube-scan-action@*` is pre-approved in enterprise policy
- **Security History:** CVE-2025-58178 (Command Injection) affected v4-v5.3.0
- [✓] **Current Version Secure:** v6.0.0 completely rewrote action from Bash to JS to prevent command injection
- [✓] **License:** LGPL-3.0

**Known Security Issues (Resolved):**
- **CVE-2025-58178** - Command Injection vulnerability
  - **Affected versions:** v4.0 through v5.3.0
  - **Severity:** High (CVSS 7.8)
  - **Fixed in:** v5.3.1 and v6.0.0
  - **Status:** [✓] Using v6.0.0 (fully patched)

**Security Measures Implemented:**
1. [✓] Pinned to full commit SHA (not tag/version)
2. [✓] Using latest secure version (v6.0.0) with command injection fix
3. [✓] Token authentication via `SONAR_TOKEN` secret
4. [✓] On Deltares enterprise allowlist

**Usage Locations:**
- [.github/workflows/rtc-tools.yml](.github/workflows/rtc-tools.yml) - `sonar` job

**Maintenance Schedule:**
- Review for updates: Monthly
- Check [release notes](https://github.com/SonarSource/sonarqube-scan-action/releases) for security fixes
- Monitor [security advisories](https://github.com/SonarSource/sonarqube-scan-action/security/advisories)
- Update commit SHA when new versions released

**Breaking Changes in v6.0.0:**
- Action rewritten from Bash to JavaScript
- Argument parsing changed - ensure proper quoting in workflow

**Last Updated:** 2025-01-15


## References

- [CVE-2025-58178 Advisory](https://github.com/SonarSource/sonarqube-scan-action/security/advisories/GHSA-f79p-9c5r-xg88)
