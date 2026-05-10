# Security Operations Guide

## Key Management

### AES-256-GCM Encryption Key
```bash
# Generate 32-byte key and encode as base64
openssl rand -base64 32

# Store in environment (never commit to repo)
export FIELD_ENCRYPTION_KEY="your-base64-encoded-key"
```

### VFD Private Key
```bash
# Generate RSA key pair for TRA VFD
openssl genrsa -out vfd_private.pem 2048
openssl rsa -in vfd_private.pem -pubout -out vfd_public.pem

# Secure permissions
chmod 600 vfd_private.pem
chown hospflow:hospflow vfd_private.pem
```

## Security Checklist

### Pre-Deployment
- [ ] Change default SECRET_KEY (min 50 chars, random)
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS (CSRF_COOKIE_SECURE=True)
- [ ] Set SESSION_COOKIE_HTTPONLY=True
- [ ] Configure HSTS (SECURE_HSTS_SECONDS=31536000)
- [ ] Enable CSP headers
- [ ] Set FIELD_ENCRYPTION_KEY
- [ ] Configure VFD private key path
- [ ] Set NHIF client credentials
- [ ] Configure SMS API keys
- [ ] Enable Sentry for production

### Ongoing Operations
- [ ] Rotate encryption keys annually
- [ ] Review audit logs weekly
- [ ] Monitor failed login attempts
- [ ] Check VFD counter integrity
- [ ] Verify NHIF token expiry
- [ ] Test SMS gateway connectivity
- [ ] Validate database backups
- [ ] Review user permissions quarterly

## Incident Response

### Suspected Data Breach
1. Immediately revoke affected user sessions
2. Check audit logs for unauthorized access patterns
3. Export audit trail for PDPC review
4. Notify PDPC within 72 hours per PDPA 2022
5. Force password reset for all users
6. Review and tighten RBAC permissions

### VFD Counter Discrepancy
1. Halt all billing operations
2. Compare GC/RCTNUM with TRA EFDMS records
3. Reconcile daily counters
4. Submit corrective Z-report if needed
5. Document incident for TRA audit

## Penetration Testing

Recommended annual testing scope:
- Authentication bypass (MFA, lockout)
- PHI field encryption validation
- API rate limiting effectiveness
- SQL injection via Django ORM
- XSS via template escaping
- CSRF token validation
- File upload restrictions
- Session fixation attacks
