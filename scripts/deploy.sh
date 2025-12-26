#!/bin/bash
# Vanguard Production Deployment Script

set -e

echo "=== Vanguard Production Deployment ==="

cd ~/Vanguard

echo "[1/6] Pulling latest code..."
git pull origin main

echo "[2/6] Stopping existing containers..."
sg docker -c 'docker-compose -f docker-compose.prod.yml down' || true

echo "[3/6] Building new images..."
sg docker -c 'docker-compose -f docker-compose.prod.yml build'

echo "[4/6] Running database migrations..."
sg docker -c 'docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput'

echo "[5/6] Collecting static files..."
sg docker -c 'docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput'

echo "[6/6] Starting containers..."
sg docker -c 'docker-compose -f docker-compose.prod.yml up -d'

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Checking container status..."
sg docker -c 'docker-compose -f docker-compose.prod.yml ps'
echo ""
echo "URLs:"
echo "  - Main Site: https://vanguard-lfg.com"
echo "  - Report: https://vanguard-lfg.com/report/"
echo "  - API Docs: https://vanguard-lfg.com/api/docs/"
