# Vanguard - Bungie.net Party Recruitment Service

A web service for Destiny 2 players to create and join fireteams using Bungie.net OAuth authentication.

**Live Site**: https://vanguard-lfg.com

## Features

- Bungie.net OAuth authentication
- Create and manage fireteam recruitment posts
- 3-tier activity selection (Activity Type → Specific Activity → Mode/Difficulty)
- Tag-based fireteam filtering
- Application system with accept/reject functionality
- Player search with Bungie.net integration
- Player profile and character display
- Statistics dashboard with distribution analysis
- REST API with Swagger/OpenAPI documentation
- Integration with Bungie.net API

## Tech Stack

- **Backend**: Django 5.x + Python 3.13
- **API**: Django REST Framework + drf-spectacular (OpenAPI)
- **Database**: SQLite
- **Statistics**: SciPy + NumPy
- **Development**: Docker
- **Local HTTPS**: ngrok (required for Bungie OAuth)

## Prerequisites

- Docker and Docker Compose
- ngrok account and installation
- Bungie.net Developer Application

## Setup Instructions

### 1. Register Bungie.net Application

1. Go to [Bungie.net Applications](https://www.bungie.net/en/Application)
2. Create a new application
3. Set the OAuth Client Type to "Confidential"
4. Note down your API Key, Client ID, and Client Secret
5. You'll update the Redirect URL after setting up ngrok

### 2. Clone and Configure

```bash
# Clone the repository
cd c:\Projects\Vanguard

# Copy environment template
cp .env.example .env

# Edit .env and add your Bungie credentials
# (You'll add the NGROK_URL later)
```

### 3. Start ngrok

```bash
# Start ngrok tunnel on port 8000
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and:
1. Update `NGROK_URL` in your `.env` file
2. Add `https://your-ngrok-url.ngrok.io/accounts/callback/` to your Bungie app's Redirect URL

### 4. Build and Run with Docker

```bash
# Build the Docker image
docker-compose build

# Run database migrations
docker-compose run web python manage.py migrate

# Create a superuser (optional, for admin access)
docker-compose run web python manage.py createsuperuser

# Start the application
docker-compose up
```

### 5. Access the Application

Open your ngrok URL in a browser: `https://your-ngrok-url.ngrok.io`

## Development

### Running Commands in Docker

```bash
# Run migrations
docker-compose run web python manage.py migrate

# Create migrations
docker-compose run web python manage.py makemigrations

# Access Django shell
docker-compose run web python manage.py shell

# Run tests
docker-compose run web python manage.py test
```

### Accessing Logs

```bash
docker-compose logs -f web
```

### Stopping the Application

```bash
docker-compose down
```

## Project Structure

```
Vanguard/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── manage.py                   # Django management script
├── vanguard/                   # Django project settings
├── accounts/                   # Authentication app (OAuth, user profiles)
├── fireteams/                  # Fireteam management app
├── players/                    # Player search and statistics app
├── templates/                  # HTML templates
│   ├── accounts/               # Profile templates
│   ├── fireteams/              # Fireteam list, detail, create, edit
│   └── players/                # Search, detail, statistics
└── static/                     # Static files (CSS, JS)
```

## Web Routes

### Authentication
- `/accounts/login/` - Initiate Bungie OAuth flow
- `/accounts/callback/` - OAuth callback handler
- `/accounts/logout/` - Logout
- `/accounts/profile/` - User profile page

### Fireteams
- `/fireteams/` - List all fireteams
- `/fireteams/create/` - Create new fireteam
- `/fireteams/<id>/` - Fireteam detail
- `/fireteams/<id>/edit/` - Edit fireteam (leader only)
- `/fireteams/<id>/delete/` - Delete fireteam (leader only)
- `/fireteams/<id>/apply/` - Apply to join fireteam
- `/fireteams/<id>/leave/` - Leave fireteam
- `/fireteams/<id>/applications/` - Manage applications (leader only)

### Players
- `/players/` - Player search
- `/players/<membership_type>/<membership_id>/` - Player profile
- `/players/statistics/` - Statistics dashboard

## REST API

API documentation available at:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

### Fireteam Endpoints
- `GET/POST /api/fireteams/` - List/Create fireteams
- `GET/PUT/DELETE /api/fireteams/<id>/` - Fireteam detail
- `POST /api/fireteams/<id>/apply/` - Apply to join
- `POST /api/fireteams/<id>/leave/` - Leave fireteam
- `GET /api/fireteams/<id>/applications/` - List applications
- `POST /api/fireteams/<id>/applications/<id>/accept/` - Accept
- `POST /api/fireteams/<id>/applications/<id>/reject/` - Reject

### Activity Endpoints
- `GET /api/activities/types/` - Activity types (Tier 1)
- `GET /api/activities/specific/` - Specific activities (Tier 2)
- `GET /api/activities/modes/` - Activity modes (Tier 3)

### Player Endpoints
- `GET /api/players/search/` - Search players
- `GET /api/players/<membership_type>/<membership_id>/` - Player detail

### Statistics Endpoints
- `GET /api/statistics/descriptive/` - Descriptive statistics
- `GET /api/statistics/class-comparison/` - Class comparison
- `GET /api/statistics/correlation/` - Correlation analysis
- `GET /api/statistics/distribution/` - Distribution data
- `GET /api/statistics/hypothesis-tests/` - Hypothesis tests

## Troubleshooting

### ngrok URL Changes
Every time you restart ngrok, you'll get a new URL. Remember to:
1. Update `NGROK_URL` in `.env`
2. Update the Redirect URL in your Bungie application
3. Restart Docker: `docker-compose restart`

### OAuth Errors
- Ensure your ngrok URL is HTTPS
- Verify the redirect URL in Bungie app matches exactly: `https://your-url.ngrok.io/accounts/callback/`
- Check that your API credentials in `.env` are correct

### Database Issues
```bash
# Reset database
docker-compose down
rm db.sqlite3
docker-compose run web python manage.py migrate
```

## Production Deployment (GCP)

### Infrastructure
| Component | Value |
|-----------|-------|
| Domain | vanguard-lfg.com |
| IP | 34.64.113.204 |
| GCP Project | vanguard-482410 |
| Instance | vanguard (e2-small) |
| Region | asia-northeast3-a (Seoul) |
| SSL | Let's Encrypt (auto-renewal) |

### Deploy Updates
```bash
# One-liner deployment
ssh vanguard-gcp "cd ~/Vanguard && git pull origin main && sg docker -c 'docker-compose up -d --build'"
```

### Server Management
```bash
# SSH access
ssh vanguard-gcp

# View logs
ssh vanguard-gcp "cd ~/Vanguard && sg docker -c 'docker-compose logs -f'"

# Restart services
ssh vanguard-gcp "cd ~/Vanguard && sg docker -c 'docker-compose restart'"

# Check status
ssh vanguard-gcp "cd ~/Vanguard && sg docker -c 'docker-compose ps'"
```

### Bungie OAuth Configuration
Production redirect URL:
```
https://vanguard-lfg.com/accounts/callback/
```