# SQLite Setup - Quick Fix for Database Error

## The Problem

You were getting this error:
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

This happened because the `.env` file was configured to use PostgreSQL, but you don't have PostgreSQL running.

## The Solution

✅ **Changed to SQLite** - No separate database server needed!

The `.env` file has been updated to use SQLite instead of PostgreSQL.

## Setup Steps

### 1. Stop Flask (if running)
Press `Ctrl+C` in the terminal where Flask is running.

### 2. Remove old migrations (if any)
```bash
rm -rf migrations/
```

### 3. Initialize the database
```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration with password support"
flask db upgrade
```

### 4. Seed with test data
```bash
flask seed-db
```

You should see output like:
```
============================================================
Database seeded successfully!
============================================================

📅 Sample Event: Annual Holiday Party 2024
🔗 Event URL: /event/xxxxx-xxxxx-xxxxx

👤 Organizer Login Credentials:
   Email: john.smith@example.com
   Password: password123
```

### 5. Start Flask again
```bash
flask run
```

### 6. Try logging in
Go to: http://localhost:5000/organizer/login

**Credentials:**
- Email: `john.smith@example.com`
- Password: `password123`

## What Changed

**Before:**
```
DATABASE_URL=postgresql://localhost/holiday_party_dev
```

**After:**
```
DATABASE_URL=sqlite:///holiday_party.db
```

## SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Setup** | ✅ Zero config | ❌ Requires server |
| **Development** | ✅ Perfect | ⚠️ Overkill |
| **Production** | ⚠️ Limited | ✅ Recommended |
| **File-based** | ✅ Yes | ❌ No |
| **Concurrent writes** | ⚠️ Limited | ✅ Excellent |

## For Production

When you're ready to deploy, switch back to PostgreSQL:

1. Install PostgreSQL
2. Create database
3. Update `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost/holiday_party_prod
   ```
4. Run migrations:
   ```bash
   flask db upgrade
   ```

## Database Location

SQLite database file: `instance/holiday_party.db`

This file contains all your data. To reset:
```bash
rm instance/holiday_party.db
flask db upgrade
flask seed-db
```

## Troubleshooting

### "No such table: persons"
Run migrations:
```bash
flask db upgrade
```

### "Database is locked"
Stop all Flask processes:
```bash
lsof -ti:5000 | xargs kill -9
```

### Start fresh
```bash
rm -rf migrations/ instance/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
flask seed-db
```

---

**Status**: ✅ SQLite configured and ready to use!  
**Next**: Run the setup steps above and try logging in again.

