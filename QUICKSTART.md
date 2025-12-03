# Vanguard - Quick Start Guide

## Prerequisites Checklist
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

✅ **Complete:**
- Docker environment
- Django project structure
- Bungie OAuth authentication
- User model with token encryption
- Party management system (models, views, admin)
- Application workflow
- Base templates and home page

⏳ **In Progress:**
- Party management templates
- User profile template

🔜 **Planned:**
- Enhanced search and filtering
- Real-time updates
- Character information display
- Notification system

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
bungie-party-recruitment/
├── accounts/          # Auth app
├── parties/           # Party app
├── vanguard/          # Django project
├── templates/         # HTML templates
├── static/            # Static files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env              # Your config
```

## Next Steps

1. Register Bungie application
2. Configure `.env` with credentials
3. Start ngrok and Docker
4. Test OAuth login
5. Create templates (see PROJECT_STATUS.md)

## Resources

- Bungie API Docs: https://bungie-net.github.io/multi/
- OAuth Guide: https://github.com/Bungie-net/api/wiki/OAuth-Documentation
- Django Docs: https://docs.djangoproject.com/

---

**Need Help?** Check PROJECT_STATUS.md for detailed information.
