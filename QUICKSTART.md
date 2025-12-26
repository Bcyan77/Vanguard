# Vanguard - Quick Start Guide

## Production URL
**Live Site**: https://vanguard-lfg.com

## Prerequisites Checklist (Local Development)
- [ ] Docker Desktop installed and running
- [ ] ngrok installed
- [ ] Bungie.net developer account created
- [ ] Bungie application registered

## Setup Steps

### 1. Configure Bungie Application
```
URL: https://www.bungie.net/en/Application
OAuth Client Type: Confidential
Redirect URL: https://YOUR-NGROK-URL.ngrok.io/accounts/callback/
```

### 2. Update .env File
```bash
BUNGIE_API_KEY=your-api-key
BUNGIE_CLIENT_ID=your-client-id
BUNGIE_CLIENT_SECRET=your-client-secret
NGROK_URL=https://your-ngrok-url.ngrok.io
```

### 3. Start Services
```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Start Django
docker-compose up
```

### 4. Access Application
```
Main Site: https://your-ngrok-url.ngrok.io
Admin: https://your-ngrok-url.ngrok.io/admin/
```

## Daily Workflow

1. Start ngrok: `ngrok http 8000`
2. Copy new ngrok URL
3. Update `.env` with new `NGROK_URL`
4. Update Bungie app redirect URL (if ngrok URL changed)
5. Start Docker: `docker-compose up`
6. Access via ngrok URL

## Common Commands

```bash
# Start development
docker-compose up

# Stop development
docker-compose down

# View logs
docker-compose logs -f web

# Run migrations
docker-compose run --rm web python manage.py migrate

# Create admin user
docker-compose run --rm web python manage.py createsuperuser

# Django shell
docker-compose run --rm web python manage.py shell

# Rebuild after dependency changes
docker-compose build
```

## Project Status

### ✅ Completed
- Docker environment
- Django project structure
- Bungie OAuth authentication
- User model with token encryption
- Fireteam management system (models, views, admin, templates)
- Application workflow with accept/reject
- 3-tier activity selection system
- Player search and profiles
- Player statistics dashboard
- REST API with Swagger/OpenAPI documentation
- All templates complete

### 🔜 Future Enhancements
- Real-time updates (WebSocket)
- Notification system
- Advanced filtering options

## Troubleshooting

**OAuth Error:**
- Verify ngrok URL in `.env` matches Bungie app
- Ensure redirect URL ends with `/accounts/callback/`
- Restart: `docker-compose restart`

**Port 8000 in use:**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Database issues:**
```bash
docker-compose down
rm db.sqlite3
docker-compose run --rm web python manage.py migrate
```

## File Structure

```
Vanguard/
├── accounts/          # Auth & user management
├── fireteams/         # Fireteam recruitment
├── players/           # Player search & statistics
├── vanguard/          # Django project settings
├── templates/         # HTML templates
├── static/            # Static files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env              # Your config
```

## Quick Access URLs

After starting the server:
- **Main Site**: `https://your-ngrok-url.ngrok.io`
- **API Docs**: `https://your-ngrok-url.ngrok.io/api/docs/`
- **Admin Panel**: `https://your-ngrok-url.ngrok.io/admin/`
- **Statistics**: `https://your-ngrok-url.ngrok.io/players/statistics/`

## GCP Production Deployment

### Server Info
- **URL**: https://vanguard-lfg.com
- **IP**: 34.64.113.204
- **Project**: vanguard-482410
- **Instance**: vanguard (asia-northeast3-a)
- **SSH Host**: `vanguard-gcp`

### Deploy Updates
```bash
# SSH into server
ssh vanguard-gcp

# Pull latest code and restart
cd ~/Vanguard
git pull origin main
sg docker -c 'docker-compose up -d --build'
```

### One-liner Deploy
```bash
ssh vanguard-gcp "cd ~/Vanguard && git pull origin main && sg docker -c 'docker-compose up -d --build'"
```

### View Logs
```bash
ssh vanguard-gcp "cd ~/Vanguard && sg docker -c 'docker-compose logs -f'"
```

### SSL Certificate
- Provider: Let's Encrypt
- Auto-renewal: Enabled (certbot)
- Expiry: 2026-03-26

## Resources

- Bungie API Docs: https://bungie-net.github.io/multi/
- OAuth Guide: https://github.com/Bungie-net/api/wiki/OAuth-Documentation
- Django Docs: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
