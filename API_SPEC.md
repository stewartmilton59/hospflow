# HospFlow API Specification

## Authentication
All API endpoints require authentication via Token Authentication header:
```
Authorization: Token <your_api_token>
```

Obtain token via:
```
POST /api/accounts/login/
{
    "email": "user@hospital.go.tz",
    "password": "your_password",
    "mfa_code": "123456"  // if MFA enabled
}
```

## Rate Limits
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Login endpoint: 5 requests/minute (brute force protection)

## Endpoints Reference

### Accounts & Identity
```
GET    /api/accounts/users/           # List users (Admin only)
POST   /api/accounts/users/           # Create user (Admin only)
GET    /api/accounts/users/{id}/      # User detail
POST   /api/accounts/login/           # Obtain auth token
POST   /api/accounts/logout/          # Revoke token
```

### Master Patient Index
```
GET    /api/patients/                 # List patients
POST   /api/patients/                 # Register new patient
GET    /api/patients/search/?q=       # Search patients
GET    /api/patients/{id}/            # Patient detail
POST   /api/patients/{id}/consent/    # Record consent (PDPA)
POST   /api/patients/{id}/consent/withdraw/  # Withdraw consent
```

### Clinical Workflows
```
GET    /api/consultations/            # List consultations
POST   /api/consultations/            # Create consultation
GET    /api/consultations/{id}/       # Consultation detail
GET    /api/consultations/icd10/?search=  # Search ICD-10 codes
POST   /api/consultations/prescriptions/  # Create prescription
POST   /api/consultations/prescriptions/{id}/dispense/  # Mark dispensed
```

### Clinical Records (Encrypted PHI)
```
GET    /api/clinical-records/         # List records
POST   /api/clinical-records/         # Create record (auto-encrypts)
GET    /api/clinical-records/{id}/    # Decrypt and view
POST   /api/clinical-records/lab-results/     # Add lab result
POST   /api/clinical-records/radiology/       # Add radiology report
```

### Billing & Fiscal Compliance
```
GET    /api/billing/invoices/         # List invoices
POST   /api/billing/invoices/         # Create invoice
GET    /api/billing/invoices/{id}/   # Invoice detail
POST   /api/billing/invoices/{id}/vfd/  # Register with TRA VFD
POST   /api/billing/z-report/{facility_id}/  # Submit daily Z-report
```

### NHIF Insurance
```
POST   /api/billing/nhif/verify/     # Verify member card
GET    /api/billing/nhif/claims/     # List claims
POST   /api/billing/nhif/claims/     # Create claim
POST   /api/billing/nhif/claims/{id}/submit/  # Submit to NHIF
```

### Inventory & Pharmacy
```
GET    /api/inventory/items/          # List items
GET    /api/inventory/batches/        # List batches
POST   /api/inventory/dispense/       # FEFO dispense medication
POST   /api/inventory/receive/        # Receive stock from MSD
POST   /api/inventory/adjustments/    # Stock adjustment
```

### Ward Management
```
GET    /api/wards/wards/              # List wards
GET    /api/wards/beds/               # List beds (real-time status)
GET    /api/wards/admissions/         # List admissions
POST   /api/wards/admissions/         # Admit patient
POST   /api/wards/admissions/{id}/discharge/  # Discharge patient
GET    /api/wards/nursing-notes/      # Nursing documentation
POST   /api/wards/mar/                # Medication Administration Record
```

### Notifications
```
GET    /api/notifications/logs/      # Notification history
POST   /api/notifications/send/      # Send test SMS
POST   /api/notifications/dlr/       # Delivery receipt webhook
```

### Audit & Compliance
```
GET    /api/audit/logs/               # Audit trail (Admin only)
GET    /api/audit/logs/?action=READ    # Filter by action
GET    /api/audit/logs/?severity=high  # Filter by severity
```

### National Reporting
```
GET    /api/reporting/dhis2/reports/  # DHIS2 submission history
GET    /api/reporting/dhis2/elements/ # Data element mappings
POST   /api/reporting/mtuha/generate/ # Generate MTUHA Book 10
POST   /api/reporting/dhis2/submit/   # Queue DHIS2 submission
GET    /api/reporting/eidsr/check/{icd10_code}/  # Check notifiable
```

## WebSocket Endpoints
```
ws://hospflow.go.tz/ws/wards/{ward_id}/  # Real-time bed updates
```

## Error Codes
| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Resource already exists (e.g., duplicate NIN) |
| 423 | Locked - Account temporarily locked |
| 429 | Too Many Requests - Rate limit exceeded |
| 502 | Bad Gateway - External API failure (TRA/NHIF/DHIS2) |
