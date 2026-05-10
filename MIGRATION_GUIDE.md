# Database Migration Guide

## Initial Setup

```bash
# Create database
createdb hospflow_db

# Create user
createuser -P hospflow_user
# Enter password when prompted

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE hospflow_db TO hospflow_user;"
```

## Django Migrations

```bash
# Generate initial migrations for all apps
python manage.py makemigrations accounts patients consultations clinical_records billing inventory notifications wards audit reporting

# Apply migrations
python manage.py migrate

# Verify
python manage.py showmigrations
```

## Data Seeding

```bash
# Create superuser
python manage.py createsuperuser

# Setup RBAC groups
python scripts/setup_rbac.py

# Import MSD catalogue
python scripts/import_msd_catalogue.py data/msd_catalogue_2026.csv

# Load ICD-10 codes
python manage.py shell << EOF
from apps.consultations.models import ICD10Code
import csv
with open('data/icd10_cm_2026.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ICD10Code.objects.get_or_create(
            code=row['code'],
            defaults={
                'description': row['description'],
                'category': row['category'][:3],
                'is_sdh': row['category'].startswith('Z5') or row['category'].startswith('Z6')
            }
        )
EOF
```

## Backup & Restore

```bash
# Backup
pg_dump -U hospflow_user -h localhost hospflow_db > hospflow_backup_$(date +%Y%m%d).sql

# Restore
psql -U hospflow_user -h localhost hospflow_db < hospflow_backup_20260510.sql

# Automated backup (cron)
0 2 * * * pg_dump -U hospflow_user hospflow_db | gzip > /backups/hospflow_$(date +%Y%m%d).sql.gz
```

## Performance Tuning

```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_patients_search ON patients_patient 
    USING gin (first_name gin_trgm_ops, last_name gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_consultations_date ON consultations_consultation (visit_date DESC);

CREATE INDEX CONCURRENTLY idx_inventory_expiry ON inventory_batch (expiry_date) 
    WHERE quantity_remaining > 0;

-- Partition audit logs by year
CREATE TABLE audit_log_2026 PARTITION OF audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```
