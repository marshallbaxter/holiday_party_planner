#!/bin/bash
# Setup script for Holiday Party Planner

echo "🎉 Setting up Holiday Party Planner..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration!"
else
    echo "✓ .env file already exists"
fi

# Create logs directory
if [ ! -d logs ]; then
    echo "📁 Creating logs directory..."
    mkdir logs
fi

# Initialize database
echo "🗄️  Initializing database..."
export FLASK_APP=run.py
flask db init 2>/dev/null || echo "✓ Database already initialized"
flask db migrate -m "Initial migration" 2>/dev/null || echo "✓ Migrations already exist"
flask db upgrade

# Seed database (optional)
read -p "🌱 Seed database with sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    flask seed-db
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Edit .env with your Brevo API key and other settings"
echo "  3. Run the application: flask run"
echo ""
echo "The application will be available at http://localhost:5000"

