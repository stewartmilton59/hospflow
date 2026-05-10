# HospFlow - Tanzania Hospital Management System

**HospFlow** is a production-grade, Django-based Hospital Management System (HMS) designed specifically for the Tanzanian healthcare ecosystem. It integrates with national infrastructures including NIDA, TRA-VFD, NHIF, and DHIS2 while ensuring full compliance with PDPA 2022 data protection regulations.

## Features

### Core Modules
- **Identity & Access Management (RBAC)**: Role-based access with Argon2 hashing, MFA, account lockout
- **Master Patient Index (MPI)**: NIDA NIN validation, biometric hooks, PDPA consent management
- **Clinical Workflows**: ICD-10-CM coding, SDoH Z-codes, vitals tracking, prescriptions
- **Clinical Records**: AES-256-GCM encrypted PHI fields, LOINC lab codes
- **Billing & Insurance**: TRA VFD fiscal compliance, NHIF electronic claims (JWE/FHIR)
- **Logistics & Pharmacy**: FEFO dispensing, MSD catalogue, race-condition-safe stock management
- **Communication**: SMS via Notify Africa, Beem Africa, FastHub (Swahili support)
- **Ward Management**: Real-time bed occupancy (WebSockets), MAR, nursing notes
- **Audit & Compliance**: Comprehensive PHI access logging, PDPA retention (25 years)
- **National Reporting**: DHIS2 integration, MTUHA Book 10, e-IDSR outbreak alerts

### Security
- AES-256-GCM field-level encryption for sensitive PHI
- Argon2 password hashing
- TLS 1.2+, HSTS, CSP headers
- Account lockout after 5 failed attempts
- Comprehensive audit trail with IP tracking

### Localization
- Full Swahili (Kiswahili) interface support
- Tanzanian Shilling (TZS) formatting
- Africa/Dar_es_Salaam timezone

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/hospflow/hospflow.git
cd hospflow

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Database setup
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Compile Swahili translations
python manage.py compilemessages

# Run server
python manage.py runserver
```

### Docker Deployment

```bash
docker-compose up -d
```

### Setup RBAC

```bash
python scripts/setup_rbac.py
```

### Import MSD Catalogue

```bash
python scripts/import_msd_catalogue.py data/msd_catalogue_2026.csv
```

## API Documentation

Access Swagger UI at: `http://localhost:8000/api/docs/`

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/accounts/login/` | Authentication |
| `GET /api/patients/` | Master Patient Index |
| `POST /api/patients/<id>/consent/` | PDPA Consent Management |
| `GET /api/consultations/` | Clinical Encounters |
| `GET /api/consultations/icd10/` | ICD-10-CM Search |
| `POST /api/billing/invoices/` | Invoice Creation |
| `POST /api/billing/invoices/<id>/vfd/` | TRA VFD Registration |
| `POST /api/billing/nhif/verify/` | NHIF Member Verification |
| `POST /api/billing/nhif/claims/<id>/submit/` | NHIF Claim Submission |
| `POST /api/inventory/dispense/` | FEFO Medication Dispensing |
| `GET /api/wards/beds/` | Real-time Bed Status |
| `GET /api/audit/logs/` | Compliance Audit Trail |

## Architecture

```
+-------------------------------------------------------------+
|                        Nginx (SSL/TLS)                       |
+-------------------------------------------------------------+
|  Django ASGI (HTTP + WebSockets)  |  Celery Workers          |
+-------------------------------------------------------------+
|  PostgreSQL 15  |  Redis (Cache + Broker)  |  File Storage  |
+-------------------------------------------------------------+
|  NIDA API  |  TRA VFD API  |  NHIF API  |  DHIS2 API      |
+-------------------------------------------------------------+
```

## Compliance

- **PDPA 2022**: Consent management, right to erasure, 25-year retention
- **TRA VFD**: Global/daily counters, SHA-1 RSA signatures, Z-reports
- **NHIF**: OAuth2 authentication, JWE encrypted FHIR bundles
- **DHIS2**: MTUHA Book 10 automation, e-IDSR outbreak tracking

## License

Proprietary - Ministry of Health, Tanzania

## Support

For support contact: stewartmilton59@gmail.com
