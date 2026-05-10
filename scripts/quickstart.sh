#!/bin/bash
# HospFlow Quick Start Script for Unix/Mac

set -e

echo "=================================="
echo "HospFlow Local Setup"
echo "=================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements/base.txt
pip install psycopg2-binary

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "WARNING: PostgreSQL not found. Please install it:"
    echo "  macOS: brew install postgresql@15"
    echo "  Ubuntu: sudo apt-get install postgresql"
    exit 1
fi

# Check if Redis is installed
if ! command -v redis-cli &> /dev/null; then
    echo "WARNING: Redis not found. Please install it:"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
    exit 1
fi

# Setup environment
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please edit it with your settings."
fi

# Create database
echo "Creating database..."
psql postgres -c "CREATE DATABASE hospflow_db;" 2>/dev/null || echo "Database already exists"
psql postgres -c "CREATE USER hospflow_user WITH PASSWORD 'hospflow123';" 2>/dev/null || echo "User already exists"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE hospflow_db TO hospflow_user;"
psql postgres -c "ALTER USER hospflow_user CREATEDB;"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Compile messages
echo "Compiling translations..."
python manage.py compilemessages

# Setup RBAC
echo "Setting up RBAC..."
python scripts/setup_rbac.py

# Load fixtures
echo "Loading sample data..."
python manage.py loaddata fixtures/initial_data.json

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Start server: python manage.py runserver"
echo "3. Start Celery: celery -A hospflow worker -l info"
echo "4. Access API docs: http://localhost:8000/api/docs/"
echo ""
echo "For full instructions, see LOCAL_SETUP.md"
