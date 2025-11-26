# Troubleshooting Guide

Common issues and solutions for the Holiday Party Planner.

## Login Issues

### ❌ "AttributeError: 'Request' object has no attribute 'session'"

**Problem**: 500 error when trying to log in.

**Solution**: ✅ **FIXED!** Changed `request.session` to `session` throughout the codebase.

**Technical Details**: In Flask, sessions are accessed via `session` (imported from Flask), not `request.session`. See `SESSION_FIX.md` for details.

---

### ❌ "Bad Request - The CSRF token is missing"

**Problem**: Form submission fails with CSRF error.

**Solution**: ✅ **FIXED!** CSRF tokens have been added to all forms.

If you still see this error:
1. Clear your browser cache and cookies
2. Restart the Flask application
3. Make sure you're using the latest version of the login template

**Technical Details**: Flask-WTF requires CSRF tokens on all POST forms for security. The login form now includes:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

---

### ❌ "No account found with that email address"

**Problem**: Login fails because user doesn't exist.

**Solutions**:
1. Make sure you ran `flask seed-db` to create test accounts
2. Check the email address for typos
3. Verify the database has data:
   ```bash
   flask shell
   ```
   ```python
   from app.models import Person
   Person.query.all()  # Should show list of people
   ```

---

### ❌ "Incorrect password"

**Problem**: Password doesn't match.

**Solutions**:
1. Default password for test accounts is: `password123`
2. Check for typos (password is case-sensitive)
3. Reset password using Flask shell:
   ```bash
   flask shell
   ```
   ```python
   from app import db
   from app.models import Person
   person = Person.query.filter_by(email='john.smith@example.com').first()
   person.set_password('newpassword')
   db.session.commit()
   ```

---

## Database Issues

### ❌ "No such table: persons"

**Problem**: Database tables don't exist.

**Solution**:
```bash
flask db upgrade
```

If that doesn't work:
```bash
# Start fresh
rm instance/holiday_party.db  # For SQLite
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask seed-db
```

---

### ❌ "Target database is not up to date"

**Problem**: Pending migrations need to be applied.

**Solution**:
```bash
flask db upgrade
```

---

### ❌ "Can't locate revision identified by..."

**Problem**: Migration history is corrupted.

**Solution**:
```bash
# Delete migrations and start fresh
rm -rf migrations/
rm instance/holiday_party.db  # For SQLite

# Reinitialize
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask seed-db
```

---

## Import Errors

### ❌ "ModuleNotFoundError: No module named 'app'"

**Problem**: Flask can't find the application.

**Solutions**:
1. Make sure virtual environment is activated:
   ```bash
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows
   ```

2. Set FLASK_APP environment variable:
   ```bash
   export FLASK_APP=run.py
   ```

3. Make sure you're in the project root directory

---

### ❌ "ImportError: cannot import name 'X' from 'app.models'"

**Problem**: Model import issue.

**Solutions**:
1. Check that all models are imported in `app/models/__init__.py`
2. Restart Flask application
3. Check for circular imports

---

## Application Errors

### ❌ "Internal Server Error" (500)

**Problem**: Something went wrong in the application.

**Solutions**:
1. Check the terminal output for error details
2. Check `logs/app.log` for error messages
3. Enable debug mode:
   ```bash
   export FLASK_ENV=development
   flask run
   ```

---

### ❌ "Address already in use"

**Problem**: Port 5000 is already being used.

**Solutions**:
1. Kill the existing Flask process:
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

2. Or use a different port:
   ```bash
   flask run --port 5001
   ```

---

## Email Issues

### ❌ "Brevo API key not configured"

**Problem**: Trying to send emails without Brevo setup.

**Solution**: This is just a warning. You can:
1. Use password login instead (no Brevo needed)
2. Configure Brevo when ready:
   - Sign up at https://www.brevo.com
   - Get API key
   - Add to `.env`:
     ```
     BREVO_API_KEY=your-key-here
     BREVO_SENDER_EMAIL=your-email@example.com
     ```

---

## Session Issues

### ❌ "Please log in to access this page"

**Problem**: Session expired or not logged in.

**Solutions**:
1. Log in again at `/organizer/login`
2. Check that cookies are enabled in your browser
3. Make sure `SECRET_KEY` is set in `.env`

---

### ❌ Session not persisting

**Problem**: Logged out immediately after login.

**Solutions**:
1. Set a strong SECRET_KEY in `.env`:
   ```
   SECRET_KEY=your-very-long-random-secret-key-here
   ```

2. Check browser cookie settings
3. Make sure you're not in incognito/private mode

---

## Development Issues

### ❌ Changes not showing up

**Problem**: Code changes not reflected in browser.

**Solutions**:
1. Hard refresh browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Restart Flask application
3. Clear browser cache
4. Check that debug mode is enabled:
   ```bash
   export FLASK_ENV=development
   ```

---

### ❌ "Template not found"

**Problem**: Flask can't find a template file.

**Solutions**:
1. Check template path is correct
2. Make sure template is in `app/templates/` directory
3. Check for typos in template name
4. Restart Flask application

---

## Quick Diagnostics

Run these commands to check your setup:

```bash
# Check Python version (should be 3.11+)
python --version

# Check Flask is installed
flask --version

# Check database exists
ls -la instance/

# Check migrations exist
ls -la migrations/versions/

# List all people in database
flask shell
>>> from app.models import Person
>>> Person.query.all()
>>> exit()

# Check if app starts
flask run
```

---

## Getting Help

If you're still stuck:

1. **Check the logs**: `logs/app.log`
2. **Enable debug mode**: `export FLASK_ENV=development`
3. **Check documentation**:
   - `README.md` - Main documentation
   - `QUICKSTART.md` - Setup guide
   - `DATABASE_MIGRATION.md` - Database help
   - `PASSWORD_LOGIN_ADDED.md` - Login details

4. **Common files to check**:
   - `.env` - Configuration
   - `config.py` - Settings
   - `run.py` - Entry point

---

## Reset Everything

If all else fails, start completely fresh:

```bash
# Deactivate virtual environment
deactivate

# Remove everything
rm -rf venv/
rm -rf migrations/
rm -rf instance/
rm -rf __pycache__/
rm -rf app/__pycache__/

# Start over
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask seed-db
flask run
```

---

**Last Updated**: 2024-11-24  
**Version**: 1.0

