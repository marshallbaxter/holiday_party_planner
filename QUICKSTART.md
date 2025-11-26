# Quick Start Guide

Get your Holiday Party Planner up and running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- A Brevo (Sendinblue) account (free tier works for MVP)

## Step 1: Initial Setup

### Option A: Using the setup script (Mac/Linux)

```bash
chmod +x setup.sh

```

### Option B: Manual setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Initialize database
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Optional: Seed with sample data
flask seed-db
```

## Step 2: Enable Persistent Sessions (Recommended for Development)

**✨ New: Sessions now persist across server restarts!** No more constant re-authentication during development.

```bash
# Quick setup (2 commands)
pip install Flask-Session==0.5.0 cachelib==0.10.2
flask run
```

**Benefits**:
- ✅ Stay logged in across server restarts
- ✅ Sessions last 7 days
- ✅ Faster development workflow

**See**: `QUICKSTART_SESSIONS.md` for details

---

## Step 3: Configure Brevo (Optional - can skip for now)

**✨ Password login is now available!** You can skip Brevo setup and start developing immediately.

When you're ready to send emails:
1. Sign up for a free Brevo account at https://www.brevo.com
2. Verify your sender email address
3. Get your API key from Settings → SMTP & API → API Keys
4. Edit `.env` and add:
   ```
   BREVO_API_KEY=your-api-key-here
   BREVO_SENDER_EMAIL=your-verified-email@example.com
   BREVO_SENDER_NAME=Your Name
   ```

## Step 3: Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run Flask development server
flask run
```

Visit http://localhost:5000 in your browser!

## Step 4: Create Your First Event

1. Go to http://localhost:5000/organizer/login
2. Log in with the test account:
   - **Email**: john.smith@example.com
   - **Password**: password123
3. You'll see the organizer dashboard with a sample event
4. Explore the seeded data:
   - Sample event URL: Check console output from `flask seed-db`
   - Other test accounts also use password: password123

## Project Structure Overview

```
holiday_party_planner/
├── app/
│   ├── models/          # Database models (Person, Event, RSVP, etc.)
│   ├── routes/          # URL routes (organizer, public, api)
│   ├── services/        # Business logic (EventService, RSVPService, etc.)
│   ├── templates/       # HTML templates
│   └── utils/           # Helper functions
├── config.py            # Configuration settings
├── run.py              # Application entry point
└── requirements.txt    # Python dependencies
```

## Common Commands

```bash
# Run development server
flask run

# Run tests
pytest

# Create database migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Seed database with sample data
flask seed-db

# Open Flask shell (for debugging)
flask shell
```

## Development Workflow

1. **Make changes** to models, routes, or templates
2. **Create migration** if you changed models: `flask db migrate -m "Description"`
3. **Apply migration**: `flask db upgrade`
4. **Test changes**: `pytest`
5. **Run app**: `flask run`

## Next Steps

### Phase 1 Tasks (Foundation)
- [ ] Implement magic link authentication
- [ ] Complete event creation form
- [ ] Add guest/household management UI
- [ ] Test email sending with Brevo

### Phase 2 Tasks (RSVP)
- [ ] Build RSVP form
- [ ] Implement RSVP submission
- [ ] Test invitation sending
- [ ] Add RSVP dashboard for organizers

### Phase 3 Tasks (Potluck)
- [ ] Create potluck item catalog UI
- [ ] Implement item claiming
- [ ] Add message wall
- [ ] Test dietary tags

### Phase 4 Tasks (Automation)
- [ ] Set up background scheduler
- [ ] Implement automated reminders
- [ ] Add guest list copying
- [ ] Test recurring events

## Troubleshooting

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
rm instance/holiday_party.db  # For SQLite
flask db upgrade
flask seed-db
```

### Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Email Not Sending
- Check Brevo API key in `.env`
- Verify sender email is confirmed in Brevo dashboard
- Check logs in `logs/app.log`

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Review the [PRD](family_holiday_party_website_prd_v_1.md) for feature specifications
- Check Flask documentation: https://flask.palletsprojects.com/

## Production Deployment

See [README.md](README.md) for production deployment checklist and instructions.

---

Happy planning! 🎉

