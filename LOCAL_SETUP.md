# HospFlow Local Development Setup

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Git

## Quick Start (5 Minutes)

### Option 1: Full Docker Setup (Recommended)

```bash
# 1. Navigate to project
cd hospflow

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env with minimal config
# Just change SECRET_KEY to something random (50+ chars)
# Everything else works with defaults for local testing

# 4. Start everything
docker-compose up -d

# 5. Run migrations inside container
docker-compose exec web python manage.py migrate

# 6. Create superuser
docker-compose exec web python manage.py createsuperuser

# 7. Load sample data
docker-compose exec web python manage.py loaddata fixtures/initial_data.json

# 8. Access the app
# API Docs: http://localhost:8000/api/docs/
# Admin: http://localhost:8000/admin/
```

### Option 2: Native Python Setup

```bash
# 1. Navigate to project
cd hospflow

# 2. Create virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements/base.txt

# 4. Install additional dev dependencies
pip install psycopg2-binary redis celery

# 5. Setup PostgreSQL locally
# macOS (with Homebrew):
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start

# Create database and user
psql postgres
CREATE DATABASE hospflow_db;
CREATE USER hospflow_user WITH PASSWORD 'hospflow123';
GRANT ALL PRIVILEGES ON DATABASE hospflow_db TO hospflow_user;
ALTER USER hospflow_user CREATEDB;
\q

# 6. Setup Redis locally
# macOS:
brew install redis
brew services start redis

# Ubuntu:
sudo apt-get install redis-server
sudo service redis-server start

# 7. Configure environment
cp .env.example .env

# Edit .env - minimum changes:
# SECRET_KEY=your-random-secret-key-here-min-50-chars-long
# DEBUG=True
# DATABASE_URL=postgres://hospflow_user:hospflow123@localhost:5432/hospflow_db
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/1

# 8. Run migrations
python manage.py migrate

# 9. Compile Swahili translations
python manage.py compilemessages

# 10. Create superuser
python manage.py createsuperuser

# 11. Setup RBAC groups
python scripts/setup_rbac.py

# 12. Load sample data
python manage.py loaddata fixtures/initial_data.json

# 13. Run development server
python manage.py runserver

# 14. In a new terminal, start Celery worker
# (Keep virtualenv activated)
celery -A hospflow worker -l info

# 15. In another terminal, start Celery beat (for scheduled tasks)
celery -A hospflow beat -l info
```

## Access Points

| URL | Purpose |
|-----|---------|
| http://localhost:8000/api/docs/ | Swagger UI - Interactive API documentation |
| http://localhost:8000/admin/ | Django Admin Panel |
| http://localhost:8000/api/accounts/login/ | API Login endpoint |
| http://localhost:8000/__debug__/ | Django Debug Toolbar (dev only) |

## Testing the API

### 1. Get Authentication Token

```bash
# Login as superuser
curl -X POST http://localhost:8000/api/accounts/login/   -H "Content-Type: application/json"   -d '{
    "email": "your-admin@email.com",
    "password": "your-password"
  }'

# Response:
# {"token": "abc123xyz789", "user": {...}}
```

### 2. Test Patient Registration (PDPA Compliance)

```bash
# Register a new patient
curl -X POST http://localhost:8000/api/patients/   -H "Content-Type: application/json"   -H "Authorization: Token abc123xyz789"   -d '{
    "nida_nin": "12345678901234567890",
    "first_name": "Juma",
    "middle_name": "Abdallah",
    "last_name": "Musa",
    "date_of_birth": "1985-03-15",
    "gender": "male",
    "phone_number": "+255712345678",
    "region": "Dar es Salaam",
    "district": "Ilala",
    "ward": "Kariakoo",
    "facility": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### 3. Record Patient Consent (PDPA 2022)

```bash
# Record explicit consent
curl -X POST http://localhost:8000/api/patients/550e8400-e29b-41d4-a716-446655440010/consent/   -H "Content-Type: application/json"   -H "Authorization: Token abc123xyz789"   -d '{
    "method": "digital"
  }'
```

### 4. Search ICD-10 Codes

```bash
# Search for malaria codes
curl "http://localhost:8000/api/consultations/icd10/?search=malaria"   -H "Authorization: Token abc123xyz789"
```

### 5. Create a Consultation

```bash
curl -X POST http://localhost:8000/api/consultations/   -H "Content-Type: application/json"   -H "Authorization: Token abc123xyz789"   -d '{
    "patient": "550e8400-e29b-41d4-a716-446655440010",
    "doctor": "your-doctor-user-id",
    "facility": "550e8400-e29b-41d4-a716-446655440000",
    "visit_date": "2026-05-10T14:00:00Z",
    "chief_complaint": "Fever and headache for 3 days",
    "priority": "urgent",
    "vital_temperature": 38.5,
    "vital_blood_pressure_sys": 120,
    "vital_blood_pressure_dia": 80,
    "vital_heart_rate": 95
  }'
```

### 6. Test NHIF Member Verification (Mock)

```bash
# Verify NHIF card (will use mock response if API unavailable)
curl -X POST http://localhost:8000/api/billing/nhif/verify/   -H "Content-Type: application/json"   -H "Authorization: Token abc123xyz789"   -d '{
    "card_number": "NHIF123456789"
  }'
```

### 7. Test Inventory FEFO Dispensing

```bash
# Dispense medication using First-Expiry-First-Out
curl -X POST http://localhost:8000/api/inventory/dispense/   -H "Content-Type: application/json"   -H "Authorization: Token abc123xyz789"   -d '{
    "prescription_id": "your-prescription-id",
    "quantity": 30
  }'
```

### 8. View Audit Logs

```bash
# View all audit logs (admin only)
curl "http://localhost:8000/api/audit/logs/"   -H "Authorization: Token abc123xyz789"

# Filter by action
curl "http://localhost:8000/api/audit/logs/?action=CREATE"   -H "Authorization: Token abc123xyz789"
```

## Running Tests

```bash
# Run all tests
python manage.py test --settings=hospflow.settings_test

# Run specific app tests
python manage.py test tests.test_accounts --settings=hospflow.settings_test
python manage.py test tests.test_patients --settings=hospflow.settings_test
python manage.py test tests.test_vfd --settings=hospflow.settings_test
python manage.py test tests.test_nhif --settings=hospflow.settings_test

# Run with coverage
coverage run --source='.' manage.py test --settings=hospflow.settings_test
coverage report
coverage html  # Generates HTML report in htmlcov/
```

## Common Issues & Fixes

### Issue: `django.db.utils.OperationalError: FATAL: database "hospflow_db" does not exist`
**Fix:**
```bash
psql postgres
CREATE DATABASE hospflow_db;
GRANT ALL PRIVILEGES ON DATABASE hospflow_db TO hospflow_user;
\q
```

### Issue: `ModuleNotFoundError: No module named 'psycopg2'`
**Fix:**
```bash
pip install psycopg2-binary
```

### Issue: `Connection refused` for Redis
**Fix:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
# macOS: brew services start redis
# Linux: sudo service redis-server start
```

### Issue: `Permission denied` on media/static directories
**Fix:**
```bash
mkdir -p media staticfiles logs
chmod 755 media staticfiles logs
```

### Issue: Swahili translations not showing
**Fix:**
```bash
python manage.py compilemessages
# Ensure locale/sw/LC_MESSAGES/django.mo is generated
```

### Issue: Celery tasks not executing
**Fix:**
```bash
# Celery worker must be running in a separate terminal
celery -A hospflow worker -l info

# For scheduled tasks, also run beat
celery -A hospflow beat -l info
```

## Development Workflow

```bash
# 1. Make code changes
# 2. Run tests
make test

# 3. Check linting
make lint

# 4. Create migrations if models changed
python manage.py makemigrations

# 5. Apply migrations
make migrate

# 6. Run server
make run
```

## Environment Variables for Local Testing

Create `.env` file with these minimum settings:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-here-change-in-production-min-50-characters
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://hospflow_user:hospflow123@localhost:5432/hospflow_db
CONN_MAX_AGE=600

# Cache
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Timezone & Language
TIME_ZONE=Africa/Dar_es_Salaam
LANGUAGE_CODE=sw

# Security (relaxed for local dev)
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False

# Encryption (generate with: openssl rand -base64 32)
FIELD_ENCRYPTION_KEY=base64-encoded-key-for-testing-only

# External APIs (use dummy values for local testing)
VFD_API_BASE_URL=https://vfd.tra.go.tz/api/v1
VFD_TAX_PAYER_ID=123-456-789
VFD_SERIAL_NUMBER=TRA-VFD-TEST-001

NHIF_API_BASE_URL=https://nhifapi.go.tz/api
NHIF_CLIENT_ID=test-client-id
NHIF_CLIENT_SECRET=test-secret
NHIF_FACILITY_CODE=TEST001

SMS_PROVIDER=notify_africa
SMS_API_KEY=test-api-key
SMS_SENDER_ID=HOSPFLW

DHIS2_BASE_URL=https://dhis2.moh.go.tz/api
DHIS2_USERNAME=test
DHIS2_PASSWORD=test
DHIS2_ORG_UNIT_ID=UID12345678
```

## Reset Everything (Clean Slate)

```bash
# Stop all services
docker-compose down -v  # If using Docker

# Or manually:
# Stop PostgreSQL: brew services stop postgresql / sudo service postgresql stop
# Stop Redis: brew services stop redis / sudo service redis-server stop

# Delete and recreate database
dropdb hospflow_db
createdb hospflow_db
psql -c "GRANT ALL PRIVILEGES ON DATABASE hospflow_db TO hospflow_user;"

# Remove migrations (optional - to start fresh)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Re-run setup
python manage.py migrate
python manage.py createsuperuser
python scripts/setup_rbac.py
python manage.py loaddata fixtures/initial_data.json
```

## Next Steps After Setup

1. **Create users with different roles** via Django Admin to test RBAC
2. **Register patients** and test NIN validation
3. **Record consent** and verify PDPA compliance in audit logs
4. **Create consultations** with ICD-10 coding
5. **Test inventory dispensing** with multiple concurrent requests
6. **Generate invoices** and test VFD receipt registration (mock)
7. **View real-time bed status** via WebSocket at `ws://localhost:8000/ws/wards/{id}/`
