# Vanguard - Bungie.net Party Recruitment Service

A web service for Destiny 2 players to create and join fireteams using Bungie.net OAuth authentication.

## Features

- 🔐 Bungie.net OAuth authentication
- 👥 Create and manage party recruitment posts
- 🏷️ Tag-based party filtering
- 📝 Application system with accept/reject functionality
- 🎮 Integration with Bungie.net API

## Tech Stack

- **Backend**: Django 5.x + Python 3.13
- **Database**: SQLite
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
cd c:\Projects\bungie-party-recruitment

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
vanguard/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── manage.py                   # Django management script
├── vanguard/                   # Django project settings
├── accounts/                   # Authentication app
├── parties/                    # Party management app
└── templates/                  # HTML templates
```

## API Endpoints

- `/accounts/login/` - Initiate Bungie OAuth flow
- `/accounts/callback/` - OAuth callback handler
- `/accounts/logout/` - Logout
- `/parties/` - List all parties
- `/parties/create/` - Create new party
- `/parties/<id>/` - Party detail
- `/parties/<id>/apply/` - Apply to join party
- `/parties/<id>/applications/` - Manage applications (leader only)

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

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License
