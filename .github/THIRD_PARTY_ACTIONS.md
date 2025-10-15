# Third-Party GitHub Actions Security Documentation

This document tracks third-party GitHub Actions used in this repository and their security vetting status, in accordance with [Deltares GitHub FAQ guidelines](https://publicwiki.deltares.nl/spaces/GIT/pages/279642305/GitHub#Pages-FAQ).

## Approved Actions

### astral-sh/setup-uv

**Current Version:** v7.1.0
**Commit SHA:** `3259c6206f993105e3a61b142c2d97bf4b9ef83d`
**Vetted Date:** 2025-01-14
**Vetted By:** [Your team/name]

**Purpose:** Sets up the uv Python package manager in GitHub Actions workflows

**Security Assessment:**
- [✓] **Verified Organization:** astral-sh is a GitHub verified organization (domain: astral.sh)
- [✓] **Repository Owner Trust:** High - 7.3k followers, creator of popular Python tools (Ruff, uv, Rye)
- [✓] **Well-Maintained:** Active development with frequent releases
- [✓] **Community Trust:** 577 stars, 56 forks, 5+ contributors
- [✓] **Security Features:**
  - SHA-256 checksum validation for downloaded binaries
  - CodeQL security scanning enabled
  - Comprehensive test coverage (Ubuntu, macOS, Windows, Alpine)
- [✓] **Clean Security History:** No published security advisories
- [✓] **Trusted Dependencies:** Uses only official GitHub Actions toolkit and Node.js libraries

**Security Measures Implemented:**
1. [✓] Pinned to full commit SHA (not tag/version)
2. [✓] Minimal permissions (read-only by default)
3. [✓] GitHub token provided for API rate limiting only
4. [✓] Caching enabled with dependency lock file

**Usage Locations:**
- [.github/actions/setup-python/action.yml](.github/actions/setup-python/action.yml)

**Maintenance Schedule:**
- Review for updates: Monthly
- Check [release notes](https://github.com/astral-sh/setup-uv/releases) for security fixes
- Update commit SHA when new versions released
- Monitor for security advisories

**Last Updated:** 2025-01-14

---

## Other Third-Party Actions Requiring Vetting

The following third-party actions are currently in use but **NOT YET** vetted and secured:

### SonarSource/sonarqube-scan-action
- **Current:** `@v5` (mutable tag)
- **Status:** Requires vetting and SHA pinning
- **Location:** `sonar` job in [.github/workflows/rtc-tools.yml](.github/workflows/rtc-tools.yml)

### pypa/gh-action-pypi-publish
- **Current:** `@release/v1` (mutable tag)
- **Status:** Requires vetting and SHA pinning
- **Location:** `deploy` job in [.github/workflows/rtc-tools.yml](.github/workflows/rtc-tools.yml)

---

## GitHub Official Actions (Recommended Enhancement)

The following GitHub official actions are **not third-party** (per Deltares definition) but should be pinned to SHA as a security enhancement:

- `actions/checkout@v4` and `@v4.1.0`
- `actions/upload-artifact@v4`
- `actions/download-artifact@v4`

**Note:** These do not require vetting per Deltares policy, but SHA pinning is recommended.

---

## Security Best Practices

All third-party actions in this repository **SHOULD** follow these security practices per Deltares guidelines:

1. **Commit SHA Pinning:** Actions are pinned to full 40-character commit SHA, not tags
2. **Minimal Permissions:** Workflow permissions explicitly scoped to minimum required
3. **Regular Updates:** Actions reviewed and updated on a regular schedule
4. **Security Vetting:** All new actions vetted according to Deltares guidelines before use
5. **Documentation:** Security assessment documented for each action

## Vetting Checklist

When adding new third-party actions, verify:

- [ ] Repository owner is trusted and verified on GitHub
- [ ] Action is well-maintained with recent activity
- [ ] Action has significant community usage (stars/forks)
- [ ] Source code has been reviewed for security concerns
- [ ] No published security advisories
- [ ] Dependencies are from trusted sources
- [ ] Action is pinned to commit SHA
- [ ] Minimal permissions configured
- [ ] Documentation added to this file

## References

- [Deltares GitHub FAQ](https://publicwiki.deltares.nl/spaces/GIT/pages/279642305/GitHub#Pages-FAQ)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
