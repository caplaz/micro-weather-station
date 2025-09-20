# Security Policy

## Supported Versions

We actively support the latest major version of this integration. Security updates are provided for:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this Home Assistant integration, please report it responsibly:

### Private Disclosure

1. **DO NOT** create a public GitHub issue
2. Email the maintainers directly at: [your-email@example.com]
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Response Time**: We will acknowledge your report within 48 hours
- **Investigation**: We will investigate and validate the vulnerability within 5 business days
- **Resolution**: Critical vulnerabilities will be patched within 7 days, others within 30 days
- **Disclosure**: We will coordinate responsible disclosure after the fix is available

### Security Best Practices

When using this integration:

1. **Keep Updated**: Always use the latest version
2. **Sensor Access**: Only grant access to necessary sensors
3. **Network Security**: Ensure your Home Assistant instance is properly secured
4. **Regular Audits**: Review which sensors the integration has access to

### Known Security Considerations

- This integration reads sensor data from your Home Assistant instance
- No external network connections are made
- All processing is done locally
- No sensitive data is transmitted or stored externally

## Security Updates

Security updates will be:

- Released as patch versions (e.g., 1.0.1 → 1.0.2)
- Documented in the CHANGELOG.md
- Announced in GitHub releases
- Tagged with "security" label

## Security Features

- Input validation for all sensor data
- Safe error handling to prevent information disclosure
- No storage of sensitive information
- Local processing only (no cloud dependencies)

---

**Note**: Replace `[your-email@example.com]` with your actual contact email before publishing.
