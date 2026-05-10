@echo off
REM HospFlow Quick Start Script for Windows

echo ==================================
echo HospFlow Local Setup
echo ==================================

REM Check Python
python --version

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements\base.txt
pip install psycopg2-binary

REM Setup environment
echo Setting up environment...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it with your settings.
)

echo.
echo ==================================
echo Manual Steps Required:
echo ==================================
echo 1. Install PostgreSQL from https://www.postgresql.org/download/windows/
echo 2. Install Redis from https://github.com/microsoftarchive/redis/releases
echo 3. Create database 'hospflow_db' and user 'hospflow_user'
echo 4. Edit .env file with your database credentials
echo 5. Run: python manage.py migrate
echo 6. Run: python manage.py createsuperuser
echo 7. Run: python scripts\setup_rbac.py
echo 8. Run: python manage.py loaddata fixtures\initial_data.json
echo 9. Run: python manage.py runserver
echo.
echo For full instructions, see LOCAL_SETUP.md
pause
