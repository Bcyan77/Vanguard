# Vanguard - Bungie.net Party Recruitment Service
## Implementation Plan

### Project Overview
A web service for Destiny 2 players to create and join fireteams using Bungie.net OAuth authentication.

**Tech Stack:**
- Backend: Django + Python 3.13
- Database: SQLite
- Development: Docker
- Local Development: ngrok (for HTTPS requirement)

---

## Phase 1: Project Setup & Docker Configuration

### 1.1 Docker Environment
- [ ] Create `Dockerfile` for Django application
- [ ] Create `docker-compose.yml` for orchestration
- [ ] Configure Python 3.13 base image
- [ ] Set up volume mappings for development
- [ ] Configure environment variables

### 1.2 Django Project Initialization
- [ ] Initialize Django project structure
- [ ] Configure settings for development
- [ ] Set up SQLite database
- [ ] Create requirements.txt with dependencies:
  - Django 5.x
  - requests (for Bungie API calls)
  - python-dotenv (for environment variables)
  - django-cors-headers (if needed for frontend)

### 1.3 Ngrok Setup
- [ ] Document ngrok setup process
- [ ] Create script to start ngrok tunnel
- [ ] Configure Django ALLOWED_HOSTS for ngrok URLs

---

## Phase 2: Bungie.net OAuth Integration

### 2.1 OAuth Configuration
- [ ] Register application on Bungie.net Developer Portal
- [ ] Store API credentials securely (environment variables)
- [ ] Configure OAuth redirect URIs (ngrok URL)

### 2.2 Authentication Flow Implementation
- [ ] Create `accounts` Django app
- [ ] Implement OAuth authorization URL generation
- [ ] Create callback view to handle OAuth code exchange
- [ ] Implement token storage (access token, refresh token, membership ID)
- [ ] Create user profile model linked to Bungie membership
- [ ] Implement token refresh mechanism

### 2.3 User Models
```python
# User model fields:
- bungie_membership_id (primary identifier)
- bungie_membership_type (platform)
- display_name
- access_token (encrypted)
- refresh_token (encrypted)
- token_expires_at
- last_login
```

---

## Phase 3: Core Party System

### 3.1 Party Models
```python
# Party model fields:
- title
- description
- activity_type (Raid, Dungeon, PvP, etc.)
- max_members
- current_members_count
- creator (ForeignKey to User)
- created_at
- scheduled_time
- status (open, full, closed, completed)

# PartyMember model:
- party (ForeignKey)
- user (ForeignKey)
- joined_at
- role (leader, member)
- status (active, left)

# PartyTag model:
- party (ForeignKey)
- tag_name (e.g., "Sherpa", "KWTD", "Chill", "Mic Required")

# PartyApplication model:
- party (ForeignKey)
- applicant (ForeignKey to User)
- message
- status (pending, accepted, rejected)
- applied_at
- reviewed_at
```

### 3.2 Party Creation & Management
- [ ] Create `parties` Django app
- [ ] Implement party creation view/form
- [ ] Add tag selection/creation functionality
- [ ] Implement party listing view (with filters)
- [ ] Create party detail view
- [ ] Add party edit/delete functionality (creator only)

### 3.3 Application System
- [ ] Create application submission view
- [ ] Implement application review interface (for party leaders)
- [ ] Add accept/reject functionality
- [ ] Implement notifications for application status changes
- [ ] Auto-update party member count on acceptance
- [ ] Prevent applications when party is full

---

## Phase 4: Frontend & Templates

### 4.1 Base Templates
- [ ] Create base template with navigation
- [ ] Implement responsive design (Bootstrap or Tailwind)
- [ ] Add user authentication status display
- [ ] Create login/logout buttons

### 4.2 Party Interface
- [ ] Party listing page with filters (activity type, tags, availability)
- [ ] Party creation form
- [ ] Party detail page showing:
  - Party information
  - Current members
  - Tags
  - Application button (if not full/not member)
  - Application management (if creator)
- [ ] User's parties dashboard (created & joined)

### 4.3 User Profile
- [ ] Display Bungie profile information
- [ ] Show user's active parties
- [ ] Application history

---

## Phase 5: API Integration & Features

### 5.1 Bungie API Integration
- [ ] Fetch user's Destiny 2 characters
- [ ] Display character information (class, light level)
- [ ] Fetch activity definitions for dropdown menus
- [ ] Implement API error handling and rate limiting

### 5.2 Enhanced Features
- [ ] Real-time party status updates
- [ ] Search and filter functionality
- [ ] Tag system with predefined and custom tags
- [ ] Party expiration (auto-close old parties)

---

## Phase 6: Security & Polish

### 6.1 Security
- [ ] Implement CSRF protection
- [ ] Secure token storage (encryption)
- [ ] Add rate limiting for API endpoints
- [ ] Validate all user inputs
- [ ] Implement proper permission checks

### 6.2 Testing
- [ ] Unit tests for models
- [ ] Integration tests for OAuth flow
- [ ] Test party creation/application workflow
- [ ] Test edge cases (full parties, expired tokens)

### 6.3 Documentation
- [ ] Setup instructions (Docker, ngrok, Bungie API)
- [ ] User guide
- [ ] API documentation
- [ ] Deployment guide

---

## File Structure
```
vanguard/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── manage.py
├── scripts/
│   └── start_ngrok.sh
├── vanguard/              # Django project
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/              # Authentication app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── bungie_oauth.py    # OAuth helper functions
├── parties/               # Party management app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── filters.py
└── templates/
    ├── base.html
    ├── accounts/
    │   ├── login.html
    │   └── profile.html
    └── parties/
        ├── list.html
        ├── detail.html
        ├── create.html
        └── dashboard.html
```

---

## Environment Variables Required
```
BUNGIE_API_KEY=your_api_key
BUNGIE_CLIENT_ID=your_client_id
BUNGIE_CLIENT_SECRET=your_client_secret
DJANGO_SECRET_KEY=your_django_secret
NGROK_URL=https://your-ngrok-url.ngrok.io
DEBUG=True
```

---

## Development Workflow
1. Start Docker containers: `docker-compose up`
2. Start ngrok tunnel: `ngrok http 8000`
3. Update NGROK_URL in .env
4. Access application via ngrok URL
5. Test OAuth flow with Bungie.net

---

## Next Steps
1. Set up Docker environment
2. Initialize Django project
3. Implement Bungie OAuth
4. Build party system
5. Create frontend templates
6. Test and refine
