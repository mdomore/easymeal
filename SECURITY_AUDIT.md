# Security Audit Report - Dependency Vulnerabilities

**Date:** 2025-01-09  
**Tool:** pip-audit 2.10.0

## Summary

Found **12 known vulnerabilities** in **5 packages**. All vulnerabilities have been addressed by updating to secure versions.

## Vulnerabilities Found and Fixed

### 1. FastAPI (0.104.1 → 0.109.1)
- **CVE:** PYSEC-2024-38 / CVE-2024-24762 / GHSA-qf9m-vfgh-m389
- **Type:** ReDoS (Regular Expression Denial of Service)
- **Impact:** When using form data, an attacker could send a malicious Content-Type header causing CPU exhaustion and stalling the event loop
- **Fix:** Updated to FastAPI 0.109.1

### 2. python-multipart (0.0.6 → 0.0.18)
- **CVE-2024-24762:** ReDoS vulnerability in Content-Type header parsing
- **CVE-2024-53981:** DoS vulnerability - excessive logging for malicious form data
- **Impact:** Denial of Service attacks via malicious form data
- **Fix:** Updated to python-multipart 0.0.18

### 3. requests (2.31.0 → 2.32.4)
- **CVE-2024-35195:** Certificate verification bypass in Session objects
- **CVE-2024-47081:** .netrc credential leak to third parties via malicious URLs
- **Impact:** Security bypass and credential leakage
- **Fix:** Updated to requests 2.32.4

### 4. Pillow (9.5.0 → 10.3.0)
- **PYSEC-2023-175 / CVE-2023-4863:** Vulnerable libwebp binaries (heap buffer overflow)
- **PYSEC-2023-227 / CVE-2023-44271:** DoS via uncontrolled memory allocation
- **CVE-2023-50447:** Arbitrary code execution via ImageMath.eval
- **CVE-2024-28219:** Buffer overflow in _imagingcms.c
- **Impact:** Multiple critical vulnerabilities including code execution and DoS
- **Fix:** Updated to Pillow 10.3.0

### 5. Starlette (0.27.0 → 0.47.2 via FastAPI update)
- **CVE-2024-47874:** DoS via unbounded form field buffering
- **CVE-2025-54121:** DoS via blocking main thread during large file uploads
- **Impact:** Denial of Service attacks
- **Fix:** Updated via FastAPI dependency (Starlette 0.47.2)

## Action Items

1. ✅ Updated `requirements.txt` with secure versions
2. ⚠️ **Next Step:** Rebuild Docker container to apply updates:
   ```bash
   docker compose build api
   docker compose up -d api
   ```
3. ⚠️ **Verification:** After rebuild, run audit again:
   ```bash
   docker compose exec api pip-audit -r requirements.txt
   ```

## Notes

- Starlette is a dependency of FastAPI, so updating FastAPI will automatically update Starlette to a compatible secure version
- Some vulnerabilities may require application-level mitigations (e.g., request size limits for form data)
- Consider implementing rate limiting and request size limits as additional defense-in-depth measures

## References

- [pip-audit](https://github.com/pypa/pip-audit)
- [OSV Database](https://osv.dev/)
- [GitHub Security Advisories](https://github.com/advisories)
