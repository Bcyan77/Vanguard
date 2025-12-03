# Vanguard Development Workflow

## Initial Setup (First Time Only)

### 1. Setup Bungie.net Application
1. Visit https://www.bungie.net/en/Application
2. Click "Create New App"
3. Fill in the application details:
   - Application name: Vanguard (or your choice)
   - Application Status: Private
   - Website: http://localhost (temporary)
   - OAuth Client Type: **Confidential**
   - Redirect URL: Leave blank for now (will update after ngrok setup)
4. Save and note down:
   - API Key
   - OAuth Client ID
   - OAuth Client Secret

### 2. Setup Local Environment
```bash
# Navigate to project directory
cd c:\Projects\bungie-party-recruitment

# Copy environment template
copy .env.example .env

# Edit .env file and add your Bungie credentials
# Leave NGROK_URL empty for now
```

### 3. Initialize Django Project
```bash
# Build Docker image
docker-compose build

# Initialize Django project structure
docker-compose run web bash scripts/init_django.sh

# This creates:
# - vanguard/ (Django project)
# - accounts/ (authentication app)
# - parties/ (party management app)
# - templates/ (HTML templates)
```

### 4. Setup ngrok
```bash
# Start ngrok on port 8000
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update .env file with NGROK_URL=https://abc123.ngrok.io
```

### 5. Update Bungie Application
1. Go back to your Bungie application settings
2. Update Redirect URL to: `https://your-ngrok-url.ngrok.io/accounts/callback/`
3. Save changes

### 6. Run Initial Migrations
```bash
# Apply database migrations
docker-compose run web python manage.py migrate

# Create admin user
docker-compose run web python manage.py createsuperuser
```

### 7. Start Development Server
```bash
docker-compose up
```

Visit your ngrok URL in a browser!

---

## Daily Development Workflow

### Starting Work
```bash
# 1. Start ngrok (in separate terminal)
ngrok http 8000

# 2. Update .env with new ngrok URL
# Edit NGROK_URL in .env file

# 3. Update Bungie app redirect URL if ngrok URL changed
# Go to https://www.bungie.net/en/Application
# Update redirect URL to: https://new-ngrok-url.ngrok.io/accounts/callback/

# 4. Start Docker containers
docker-compose up
```

### Making Changes

#### Database Changes
```bash
# After modifying models.py files
docker-compose run web python manage.py makemigrations
docker-compose run web python manage.py migrate
```

#### Installing New Packages
```bash
# 1. Add package to requirements.txt
# 2. Rebuild Docker image
docker-compose build
# 3. Restart containers
docker-compose up
```

#### Running Tests
```bash
docker-compose run web python manage.py test
```

#### Accessing Django Shell
```bash
docker-compose run web python manage.py shell
```

#### Viewing Logs
```bash
# Follow logs
docker-compose logs -f web

# View last 100 lines
docker-compose logs --tail=100 web
```

### Stopping Work
```bash
# Stop containers (Ctrl+C in terminal running docker-compose up)
# Or in another terminal:
docker-compose down

# Stop ngrok (Ctrl+C in ngrok terminal)
```

---

## Common Tasks

### Reset Database
```bash
docker-compose down
# Delete db.sqlite3 file
docker-compose run web python manage.py migrate
docker-compose run web python manage.py createsuperuser
```

### Access Django Admin
1. Visit `https://your-ngrok-url.ngrok.io/admin/`
2. Login with superuser credentials

### Create New Django App
```bash
docker-compose run web python manage.py startapp app_name
# Then add 'app_name' to INSTALLED_APPS in vanguard/settings.py
```

### Collect Static Files (for production)
```bash
docker-compose run web python manage.py collectstatic
```

---

## Troubleshooting

### "Invalid redirect_uri" error
- Ensure ngrok URL in `.env` matches the one in Bungie app settings
- Verify redirect URL ends with `/accounts/callback/`
- Restart Docker: `docker-compose restart`

### "Application not found" error
- Check BUNGIE_CLIENT_ID in `.env` matches your Bungie app
- Verify API key is correct

### Port 8000 already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Docker build fails
```bash
# Clean Docker cache
docker-compose down
docker system prune -a
docker-compose build --no-cache
```

### Database locked error
```bash
# Stop all containers
docker-compose down

# Remove database file
rm db.sqlite3

# Recreate database
docker-compose run web python manage.py migrate
```

---

## Development Tips

1. **Keep ngrok running**: Don't close the ngrok terminal while developing
2. **Free ngrok URLs expire**: Free ngrok URLs change each restart, requiring Bungie app update
3. **Use ngrok paid plan**: For a persistent URL that doesn't change
4. **Check logs**: Always check `docker-compose logs` when debugging
5. **Test OAuth flow**: Test login/logout frequently during development
6. **Use Django Debug Toolbar**: Consider adding for development debugging

---

## Next Implementation Steps

Follow the IMPLEMENTATION_PLAN.md for detailed development phases:
1. ✅ Phase 1: Project Setup & Docker Configuration
2. ⏳ Phase 2: Bungie.net OAuth Integration
3. ⏳ Phase 3: Core Party System
4. ⏳ Phase 4: Frontend & Templates
5. ⏳ Phase 5: API Integration & Features
6. ⏳ Phase 6: Security & Polish
