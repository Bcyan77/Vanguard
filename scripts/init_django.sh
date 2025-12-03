#!/bin/bash

# This script initializes the Django project structure
# Run this with: docker-compose run web bash scripts/init_django.sh

echo "Creating Django project..."
django-admin startproject vanguard .

echo "Creating accounts app..."
python manage.py startapp accounts

echo "Creating parties app..."
python manage.py startapp parties

echo "Creating templates directory..."
mkdir -p templates/accounts templates/parties templates/static

echo "Django project initialized successfully!"
echo "Next steps:"
echo "1. Update vanguard/settings.py with app configurations"
echo "2. Run migrations: docker-compose run web python manage.py migrate"
echo "3. Create superuser: docker-compose run web python manage.py createsuperuser"
