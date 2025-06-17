# Security Policy

## Supported Versions

This is a demonstration project for educational purposes. Security updates will be provided on a best-effort basis.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

This is a demonstration project intended for learning purposes. However, we take security seriously even in demo code.

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email the details to: security@example.com (replace with your actual contact)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide updates on the fix.

## Security Best Practices

When deploying this demo:

1. **Never use the default SECRET_KEY** - Always generate a new one
2. **Set DEBUG=False** in production
3. **Use environment variables** for all sensitive configuration
4. **Enable HTTPS** in production
5. **Implement rate limiting** for API endpoints
6. **Regular security updates** - Keep all dependencies updated

## Known Security Considerations

- This demo uses SQLite - for production, use PostgreSQL or MySQL
- JWT tokens have a 60-minute expiration - adjust based on your needs
- No rate limiting is implemented - add for production use
- CORS is configured for development - restrict in production