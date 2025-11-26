#!/bin/bash

# Setup script for persistent sessions
# This script installs Flask-Session and sets up the session directory

set -e  # Exit on error

echo "============================================================"
echo "Setting up Persistent Sessions for Holiday Party Planner"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo "📦 Installing Flask-Session and dependencies..."
pip install Flask-Session==0.5.0 cachelib==0.10.2

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Create session directory
echo "📁 Creating session directory..."
mkdir -p flask_session
echo "✅ Session directory created: flask_session/"
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python -c "import flask_session; print(f'Flask-Session version: {flask_session.__version__}')" 2>/dev/null || {
    echo "❌ Flask-Session not installed correctly"
    exit 1
}

echo "✅ Flask-Session installed and verified!"
echo ""

# Check if .gitignore includes flask_session
if grep -q "flask_session/" .gitignore 2>/dev/null; then
    echo "✅ flask_session/ already in .gitignore"
else
    echo "⚠️  Warning: flask_session/ not in .gitignore"
    echo "Add this line to .gitignore:"
    echo "  flask_session/"
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Restart Flask: flask run"
echo "2. Log in: http://localhost:5000/organizer/login"
echo "3. Test: Restart Flask and verify you're still logged in"
echo ""
echo "📚 Documentation: See SESSION_PERSISTENCE.md for details"
echo ""

