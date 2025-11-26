# Holiday Party Planner - Project Structure

Complete overview of the Flask application structure and architecture.

## Directory Structure

```
holiday_party_planner/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── person.py           # Person model (adults & children)
│   │   ├── household.py        # Household & HouseholdMembership models
│   │   ├── event.py            # Event model
│   │   ├── event_admin.py      # EventAdmin & EventInvitation models
│   │   ├── rsvp.py             # RSVP model
│   │   ├── potluck.py          # PotluckItem & PotluckClaim models
│   │   ├── message.py          # MessageWallPost model
│   │   └── notification.py     # Notification audit log model
│   ├── routes/                  # Blueprint routes
│   │   ├── __init__.py
│   │   ├── organizer.py        # Organizer dashboard & management
│   │   ├── public.py           # Public event pages & RSVP
│   │   └── api.py              # API endpoints & webhooks
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── event_service.py    # Event management logic
│   │   ├── rsvp_service.py     # RSVP management logic
│   │   ├── invitation_service.py # Invitation sending logic
│   │   ├── notification_service.py # Email/SMS sending via Brevo
│   │   └── potluck_service.py  # Potluck item management
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html           # Base template with navigation
│   │   ├── public/             # Public-facing templates
│   │   │   └── index.html      # Homepage
│   │   ├── organizer/          # Organizer dashboard templates
│   │   │   ├── login.html      # Login page
│   │   │   └── dashboard.html  # Event list dashboard
│   │   ├── emails/             # Email templates
│   │   │   ├── invitation.html
│   │   │   ├── rsvp_confirmation.html
│   │   │   └── household_rsvp_confirmation.html
│   │   └── errors/             # Error page templates
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   ├── static/                  # Static files (CSS, JS, images)
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── decorators.py       # Custom route decorators
│   │   └── seed.py             # Database seeding for development
│   └── scheduler.py             # Background job scheduler (APScheduler)
├── migrations/                  # Database migrations (Flask-Migrate)
├── tests/                       # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── test_models.py          # Model tests
├── logs/                        # Application logs (gitignored)
├── instance/                    # Instance-specific files (gitignored)
├── config.py                    # Application configuration
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── pytest.ini                   # Pytest configuration
├── setup.sh                     # Setup script
├── README.md                    # Main documentation
├── QUICKSTART.md               # Quick start guide
└── PROJECT_STRUCTURE.md        # This file
```

## Key Components

### 1. Application Factory (`app/__init__.py`)

- Creates and configures Flask application
- Initializes extensions (SQLAlchemy, Flask-Migrate, Flask-Mail, CSRF)
- Registers blueprints
- Configures logging and error handlers
- Registers template filters and context processors

### 2. Database Models (`app/models/`)

**Core Models:**
- `Person`: Individual (adult or child)
- `Household`: Group of people
- `HouseholdMembership`: Many-to-many relationship between Person and Household
- `Event`: Holiday party event
- `EventAdmin`: Admin/organizer access to events
- `EventInvitation`: Invitation sent to household with RSVP token
- `RSVP`: Individual RSVP response
- `PotluckItem`: Potluck dish/item
- `PotluckClaim`: Claim on a potluck item
- `MessageWallPost`: Message on event wall
- `Notification`: Audit log for sent emails/SMS

### 3. Routes (`app/routes/`)

**Organizer Blueprint** (`/organizer`):
- Dashboard, event management, guest management
- Requires authentication

**Public Blueprint** (`/`):
- Event detail pages, RSVP forms, potluck lists
- Token-based access for guests

**API Blueprint** (`/api`):
- Health check, webhooks, AJAX endpoints
- JSON responses

### 4. Services (`app/services/`)

Business logic layer that handles:
- Event creation, updating, publishing
- RSVP management and statistics
- Invitation generation and sending
- Email/SMS notifications via Brevo
- Potluck item management

### 5. Configuration (`config.py`)

Three environments:
- `DevelopmentConfig`: Debug mode, SQLite, verbose logging
- `TestingConfig`: In-memory database, CSRF disabled
- `ProductionConfig`: PostgreSQL, security checks

### 6. Background Scheduler (`app/scheduler.py`)

APScheduler-based background jobs:
- Daily reminder checks (RSVP deadlines, potluck reminders)
- Automatic event archiving
- Configurable run time via `REMINDER_CHECK_HOUR`

## Data Flow

### Event Creation Flow
```
Organizer → Create Event Form → EventService.create_event()
  → Event + EventAdmin created → Database
```

### Invitation Flow
```
Organizer → Select Guests → InvitationService.create_invitations_bulk()
  → EventInvitation + RSVP records created
  → NotificationService.send_invitation_email()
  → Brevo API → Email sent to household
```

### RSVP Flow
```
Guest clicks email link → Token verified → RSVP form displayed
  → Guest submits → RSVPService.update_household_rsvps()
  → Database updated → NotificationService.send_rsvp_confirmation()
  → Confirmation email sent
```

### Reminder Flow
```
Scheduler runs daily → check_and_send_reminders()
  → Query events with upcoming deadlines
  → NotificationService.send_rsvp_reminders()
  → Brevo API → Reminder emails sent
```

## Security Features

1. **CSRF Protection**: Flask-WTF CSRF tokens on all forms
2. **Token-Based Access**: Signed tokens for guest RSVP access
3. **Unlisted URLs**: UUID-based event URLs (not sequential IDs)
4. **Session Management**: Secure session cookies for organizers
5. **Input Validation**: WTForms validation on all user inputs
6. **SQL Injection Protection**: SQLAlchemy ORM parameterized queries

## Extension Points

### Adding a New Feature

1. **Model**: Create model in `app/models/`
2. **Service**: Add business logic in `app/services/`
3. **Routes**: Add routes in appropriate blueprint
4. **Templates**: Create HTML templates
5. **Migration**: Run `flask db migrate`
6. **Tests**: Add tests in `tests/`

### Adding a New Email Template

1. Create HTML template in `app/templates/emails/`
2. Add method in `NotificationService`
3. Call from appropriate service or route

### Adding a New Background Job

1. Add scheduled job in `app/scheduler.py`
2. Use `@scheduler.scheduled_job()` decorator
3. Wrap in `with app.app_context():`

## Testing Strategy

- **Unit Tests**: Test individual models and services
- **Integration Tests**: Test routes and full workflows
- **Fixtures**: Reusable test data in `tests/conftest.py`
- **Coverage**: Aim for >80% code coverage

## Performance Considerations

- **Database Indexes**: Added on frequently queried fields
- **Lazy Loading**: Relationships use `lazy='dynamic'` where appropriate
- **Query Optimization**: Use `joinedload()` for eager loading when needed
- **Caching**: Consider Flask-Caching for production

## Deployment Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Configure Brevo API key
- [ ] Set up gunicorn/uwsgi
- [ ] Configure nginx reverse proxy
- [ ] Enable HTTPS/TLS
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy
- [ ] Test email sending
- [ ] Test background scheduler

## Development Best Practices

1. **Always use virtual environment**
2. **Run migrations after model changes**
3. **Write tests for new features**
4. **Use services for business logic** (not in routes)
5. **Keep templates simple** (logic in views/services)
6. **Log important events** (use `app.logger`)
7. **Handle errors gracefully** (try/except blocks)
8. **Validate user input** (WTForms)
9. **Use type hints** (for better IDE support)
10. **Document complex logic** (docstrings)

