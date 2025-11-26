#!/bin/bash
# Reset and initialize SQLite database

echo "🗄️  Resetting database..."

# Remove old database and migrations
echo "Removing old database and migrations..."
rm -rf migrations/
rm -rf instance/

# Set Flask app
export FLASK_APP=run.py

# Initialize migrations
echo "Initializing migrations..."
flask db init

# Create migration
echo "Creating migration..."
flask db migrate -m "Initial migration with password support"

# Apply migration
echo "Applying migration..."
flask db upgrade

# Seed database
echo "Seeding database with test data..."
flask seed-db

echo ""
echo "✅ Database reset complete!"
echo ""
echo "You can now run: flask run"
echo "Then log in at: http://localhost:5000/organizer/login"
echo ""
echo "Credentials:"
echo "  Email: john.smith@example.com"
echo "  Password: password123"
echo ""

