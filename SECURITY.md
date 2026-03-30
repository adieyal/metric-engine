# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Metric Engine seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email:** adi@burgercom.co.za
- **Subject:** [SECURITY] Metric Engine - Brief description

### What to Include

Please include the following information to help us better understand the nature and scope of the issue:

- **Type of issue** (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- **Full paths of source file(s)** related to the manifestation of the issue
- **The location** of the affected source code (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the issue**, including how an attacker might exploit it

This information will help us triage your report more quickly.

### What to Expect

After you submit a report, you should expect:

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 3 business days
2. **Assessment**: We will confirm the problem and determine affected versions within 1 week
3. **Fix**: We will work on a fix and prepare a security advisory
4. **Release**: We will release a patched version
5. **Disclosure**: We will publicly disclose the vulnerability in a coordinated manner

### Timeline

- **Initial Response:** Within 3 business days
- **Status Update:** Within 7 days
- **Fix Timeline:** Depends on severity (Critical: 7-14 days, High: 14-30 days, Medium/Low: next regular release)

## Security Considerations for Users

### Input Validation

While Metric Engine handles invalid mathematical operations gracefully (e.g., division by zero), you should still validate inputs in your application:

```python
from metricengine import FinancialValue as FV

# Good: Validate before processing
if not user_input or not isinstance(user_input, (int, float, Decimal)):
    raise ValueError("Invalid input")

value = FV(user_input)
```

### Provenance Data

Provenance tracking may store metadata about calculations. Be careful not to include sensitive information in metadata:

```python
# Bad: Including sensitive data in metadata
result = calculate_with_meta(
    value,
    meta={"user_ssn": "123-45-6789"}  # Don't do this!
)

# Good: Only include non-sensitive operational data
result = calculate_with_meta(
    value,
    meta={"calculation_id": "calc_001", "timestamp": datetime.now()}
)
```

### Calculation Injection

If you're building calculation functions from user input, ensure proper validation:

```python
# Bad: Directly using user input in calculations
user_formula = request.get("formula")  # Dangerous!
exec(user_formula)  # Never do this!

# Good: Use the calculation engine with pre-registered calculations
allowed_calculations = ["gross_profit", "gross_margin"]
calc_name = request.get("calculation")
if calc_name in allowed_calculations:
    result = engine.calculate(calc_name, data)
```

### Decimal Overflow

Be aware of potential decimal overflow with very large numbers:

```python
from decimal import Decimal, getcontext

# Set appropriate precision for your use case
getcontext().prec = 28  # Default, adjust if needed
```

### Dependency Security

Keep dependencies up to date:

```bash
# Check for security vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

## Known Security Considerations

### Not Cryptographically Secure

The hashing used in provenance tracking is for data integrity and deduplication, **not** for cryptographic security. Do not rely on it for security-critical purposes.

### Pickle Deserialization

This library does not use pickle for serialization. If you choose to serialize FinancialValue objects using pickle, be aware of the standard pickle security concerns.

### No SQL Injection Risk

Metric Engine is a pure calculation library with no database interaction. However, if you store FinancialValue data in a database, follow your database's security best practices.

## Security Update Policy

- **Critical vulnerabilities:** Immediate patch release
- **High severity:** Patch within 14 days
- **Medium severity:** Patch in next minor release
- **Low severity:** Patch in next release (minor or major)

## Security Acknowledgments

We appreciate the efforts of security researchers and users who help keep Metric Engine secure. Contributors who responsibly disclose security issues will be acknowledged in:

- The security advisory
- The CHANGELOG.md
- This SECURITY.md file (if they wish)

## Security Best Practices for Contributors

If you're contributing to Metric Engine:

1. **Never commit secrets** (API keys, passwords, tokens)
2. **Validate all inputs** in new features
3. **Follow secure coding practices**
4. **Add tests for edge cases** and potential security issues
5. **Review dependencies** for known vulnerabilities
6. **Use type hints** to catch potential type-related issues

## Resources

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)

## Past Security Issues

No security issues have been reported yet (v0.1.x is the first release).

---

Thank you for helping keep Metric Engine secure! 🔒
