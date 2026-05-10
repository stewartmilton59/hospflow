.PHONY: help install migrate run test lint docker-build docker-up clean

help:
	@echo "HospFlow - Tanzania Hospital Management System"
	@echo ""
	@echo "Available targets:"
	@echo "  install       Install Python dependencies"
	@echo "  migrate       Run database migrations"
	@echo "  run           Start development server"
	@echo "  test          Run test suite"
	@echo "  lint          Run code linting"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start Docker containers"
	@echo "  clean         Clean generated files"
	@echo "  setup         Full initial setup"

install:
	pip install -r requirements/base.txt

migrate:
	python manage.py migrate
	python manage.py compilemessages

run: migrate
	python manage.py runserver

test:
	python manage.py test --settings=hospflow.settings_test

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check .

docker-build:
	docker build -t hospflow:latest .

docker-up:
	docker-compose up -d

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.mo" -delete
	rm -rf staticfiles/

setup: install migrate
	python scripts/setup_rbac.py
	python manage.py loaddata fixtures/initial_data.json
	@echo "Setup complete. Create superuser with: python manage.py createsuperuser"
