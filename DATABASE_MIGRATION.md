# Database Migration Guide

## Initial Setup (First Time)

If you're setting up the database for the first time:

```bash
# Set Flask app
export FLASK_APP=run.py

# Initialize migrations folder
flask db init

# Create initial migration
flask db migrate -m "Initial migration with password support"

# Apply migration
flask db upgrade

# Seed with sample data (includes test accounts with passwords)
flask seed-db
```

## Adding Password Field to Existing Database

If you already have a database without the password field, you need to create a migration:

```bash
# Create migration for password field
flask db migrate -m "Add password_hash to Person model"

# Review the migration file in migrations/versions/
# It should add a password_hash column to the persons table

# Apply the migration
flask db upgrade
```

## Setting Passwords for Existing Users

If you have existing users without passwords, you can set them using the Flask shell:

```bash
flask shell
```

Then in the Python shell:

```python
from app import db
from app.models import Person

# Find a person by email
person = Person.query.filter_by(email='john.smith@example.com').first()

# Set their password
person.set_password('your-password-here')

# Save to database
db.session.commit()

# Exit shell
exit()
```

## Test Login Credentials (After Seeding)

After running `flask seed-db`, you can log in with:

- **Email**: john.smith@example.com
- **Password**: password123

Other test accounts (all use password: password123):
- jane.smith@example.com
- bob.johnson@example.com
- alice.johnson@example.com
- mary.williams@example.com

## Resetting the Database

If you need to start fresh:

```bash
# For SQLite (development)
rm instance/holiday_party.db

# For PostgreSQL (production)
# DROP DATABASE holiday_party_dev;
# CREATE DATABASE holiday_party_dev;

# Then re-run migrations
flask db upgrade
flask seed-db
```

## Migration Best Practices

1. **Always review migrations** before applying them
2. **Backup your database** before running migrations in production
3. **Test migrations** in development first
4. **Never edit applied migrations** - create new ones instead
5. **Commit migration files** to version control

## Common Issues

### Issue: "Can't locate revision identified by..."
**Solution**: Delete the `migrations/` folder and start fresh with `flask db init`

### Issue: "Target database is not up to date"
**Solution**: Run `flask db upgrade` to apply pending migrations

### Issue: "No changes in schema detected"
**Solution**: Make sure your model changes are imported in `run.py` or `app/__init__.py`

## Migration Commands Reference

```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade

# Show current migration version
flask db current

# Show migration history
flask db history
```

