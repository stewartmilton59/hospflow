# HospFlow System Architecture

## Overview
HospFlow is built on Django's "shared-nothing" architecture enabling horizontal scalability across application, database, and cache layers.

## Layer Architecture

### Presentation Layer
- **Nginx**: SSL termination, load balancing, rate limiting, static file serving
- **Django ASGI**: Handles both HTTP and WebSocket connections via Daphne
- **Django WSGI**: Fallback for traditional synchronous requests via Gunicorn

### Application Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    Django Application Layer                    │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Accounts │ Patients │ Clinical │ Billing  │ Inventory       │
│ (RBAC)   │ (MPI)    │ (ICD10)  │ (VFD/    │ (FEFO/MSD)      │
│          │          │          │  NHIF)   │                 │
├──────────┼──────────┼──────────┼──────────┼─────────────────┤
│ Wards    │ Notif.   │ Audit    │ Report.  │ Common          │
│ (MAR)    │ (SMS)    │ (PDPA)   │ (DHIS2)  │ (Encryption)    │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
```

### Data Layer
- **PostgreSQL 15**: Primary relational database with persistent connections (CONN_MAX_AGE=600)
- **Redis**: Session cache, query cache, Celery message broker
- **File Storage**: Secure non-executable storage for clinical artifacts (radiology, lab reports)

### Integration Layer
- **NIDA CIG**: Biometric verification via Common Interface Gateway
- **TRA EFDMS**: Virtual Fiscal Device with PKI digital signatures
- **NHIF Breeze API**: OAuth2 member verification and JWE claim submission
- **DHIS2**: Aggregate health data reporting and e-IDSR outbreak tracking

## Security Architecture

### Defense in Depth
```
Layer 1: Network (TLS 1.2+, HSTS, CSP, WAF)
Layer 2: Application (RBAC, MFA, Argon2, CSRF)
Layer 3: Data (AES-256-GCM field encryption, audit logging)
Layer 4: Infrastructure (Docker, non-root user, read-only volumes)
```

### Encryption Strategy
- **At Rest**: AES-256-GCM for PHI fields (diagnosis, vitals, prescriptions)
- **In Transit**: TLS 1.2+ with HSTS preload
- **Keys**: AWS KMS or environment variables (never in source code)

## Scalability Patterns
- **Horizontal**: Multiple Django instances behind Nginx load balancer
- **Database**: Read replicas for reporting queries
- **Caching**: Redis for sessions, template fragments, and query results
- **Async**: Celery workers for SMS, reports, and NHIF submissions
- **Real-time**: ASGI + WebSockets for live bed occupancy dashboards

## Data Flow Examples

### Patient Registration Flow
```
Receptionist → Patient Form → NIN Validation → NIDA CIG Check
                                    ↓
                        PDPA Consent Recorded
                                    ↓
                        MPI Created (UUID PK)
                                    ↓
                        SMS Confirmation Sent
```

### Clinical Encounter Flow
```
Nurse → Vitals Captured → Doctor → ICD-10 Diagnosis → Prescription
                                        ↓
                              Notifiable Disease Check
                                        ↓
                              e-IDSR Alert (if outbreak-prone)
                                        ↓
                              Pharmacy → FEFO Dispensing
```

### Billing Flow
```
Consultation → Invoice Generated → VFD Registration (TRA)
                                        ↓
                              NHIF Verification (if applicable)
                                        ↓
                              Claim Submission (JWE/FHIR)
                                        ↓
                              Z-Report at End of Day
```

## Compliance Mapping

| Requirement | Technical Implementation |
|-------------|-------------------------|
| PDPA 2022 Section 5 | ConsentLog model with timestamps |
| PDPA Right to Erasure | consent_withdrawn flag + audit trail |
| 25-Year Retention | retention_until field in AuditLog |
| TRA VFD GC/RCTNUM | VFDCounter with atomic increment |
| TRA VFD Signature | SHA-1 RSA + Base64 encoding |
| NHIF OAuth2 | NHIFService._get_token() with expiry |
| NHIF FHIR Claims | JSON bundle encrypted as JWE |
| DHIS2 MTUHA Book 10 | Django ORM aggregation + API submission |
| e-IDSR Alerts | Automatic DHIS2 Tracker registration |
