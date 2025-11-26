# Family Holiday Party Planner

A lightweight, privacy-respecting web application for planning and managing family holiday events. Built with Flask and Python.

## Features

- 🎉 **Event Management**: Create and manage holiday party events
- 📧 **Email Invitations**: Send invitations via Brevo (Sendinblue)
- 👨‍👩‍👧‍👦 **Household-Aware RSVPs**: Manage RSVPs by household with adult/child roles
- 🍽️ **Potluck Coordination**: Organize potluck items with dietary tags
- 🔔 **Automated Reminders**: Background jobs for RSVP and potluck reminders
- 🔗 **Unlisted Event Links**: Privacy-focused access control
- 📋 **Guest List Management**: Copy guest lists year-to-year with deduplication

## Technology Stack

- **Backend**: Flask 3.0, Python 3.11+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Email**: Brevo (Sendinblue) API
- **Background Jobs**: APScheduler
- **Frontend**: Jinja2 templates, Tailwind CSS, HTMX
- **ORM**: SQLAlchemy with Flask-Migrate

## Project Structure

```
holiday_party_planner/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models/               # SQLAlchemy models
│   │   ├── person.py
│   │   ├── household.py
│   │   ├── event.py
│   │   ├── rsvp.py
│   │   ├── potluck.py
│   │   └── ...
│   ├── routes/               # Blueprint routes
│   │   ├── organizer.py      # Organizer dashboard routes
│   │   ├── public.py         # Public event pages
│   │   └── api.py            # API endpoints
│   ├── services/             # Business logic layer
│   │   ├── event_service.py
│   │   ├── rsvp_service.py
│   │   ├── invitation_service.py
│   │   └── notification_service.py
│   ├── templates/            # Jinja2 templates
│   ├── static/               # Static files (CSS, JS, images)
│   ├── utils/                # Utilities and helpers
│   └── scheduler.py          # Background job scheduler
├── migrations/               # Database migrations
├── tests/                    # Unit and integration tests
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── run.py                    # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for development)
- Brevo (Sendinblue) account and API key

### Installation

1. **Clone the repository**
   ```bash
   cd holiday_party_planner
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Seed the database (optional)**
   ```bash
   flask seed-db
   ```

7. **Run the application**
   ```bash
   flask run
   ```

   The application will be available at `http://localhost:5000`

## Configuration

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string
- `BREVO_API_KEY`: Brevo API key for email sending
- `BREVO_SENDER_EMAIL`: Verified sender email address
- `FLASK_ENV`: Environment (development, production, testing)

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Code Quality

```bash
# Format code with Black
black app/

# Lint with Flake8
flake8 app/
```

## Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up Brevo API key and verify sender domain
- [ ] Configure gunicorn or another WSGI server
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Enable HTTPS/TLS
- [ ] Configure logging
- [ ] Set up monitoring

### Example Production Command

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

## Roadmap

### Phase 1: Foundation (Weeks 1-3) ✅
- [x] Database schema and models
- [x] Flask application structure
- [x] Basic routes and templates
- [ ] Organizer authentication
- [ ] Event CRUD operations

### Phase 2: Invitations & RSVP (Weeks 4-5)
- [ ] Email invitation templates
- [ ] Brevo integration
- [ ] RSVP form and submission
- [ ] RSVP confirmation emails

### Phase 3: Potluck Coordination (Weeks 6-7)
- [ ] Potluck item catalog
- [ ] Item claiming functionality
- [ ] Message wall

### Phase 4: Automation (Weeks 8-10)
- [ ] Background job system
- [ ] Automated reminders
- [ ] Guest list copying
- [ ] Recurring event creation

## Contributing

This is a personal/family project. If you'd like to contribute, please reach out!

## License

Private project - All rights reserved

## Support

For questions or issues, contact: [your-email@example.com]

