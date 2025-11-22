#!/bin/bash
# setup.sh - Fixed for Separate Core Logic

set -e  # Exit on error

echo "======================================="
echo "  Stock Market Analysis Setup"
echo "======================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found!"
    echo "Please run this script from the Stock_market_frontend directory"
    exit 1
fi

# Create virtual environment (if not exists)
if [ ! -d "venv" ]; then
    echo "[1/8] 📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created!"
else
    echo "[1/8] ✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "[2/8] 🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo ""

# Install dependencies
echo "[3/8] 📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed!"
echo ""

# Generate SECRET_KEY
echo "[4/8] 🔑 Generating SECRET_KEY..."
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
echo "Generated SECRET_KEY:"
echo "$SECRET_KEY"
echo ""
echo "⚠️  ACTION REQUIRED: Add this to your .env file:"
echo "SECRET_KEY=$SECRET_KEY"
echo ""
read -p "Press Enter when done..."
echo ""

# Create necessary directories (skip core - it's separate)
echo "[5/8] 📁 Creating directories..."
mkdir -p web/templates
mkdir -p web/static/css
mkdir -p web/static/js
mkdir -p locale
mkdir -p media
mkdir -p staticfiles
echo "✅ Directories created!"
echo ""

# Check/Create manage.py
echo "[6/8] 🔧 Checking Django setup..."
if [ ! -f "manage.py" ]; then
    echo "⚠️  manage.py not found! Creating it..."
    cat > manage.py << 'EOF'
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
EOF
    chmod +x manage.py
    echo "✅ manage.py created!"
else
    echo "✅ manage.py exists!"
fi
echo ""

# Django migrations
echo "[7/8] 🗄️  Running Django migrations..."
python manage.py makemigrations
python manage.py migrate
echo "✅ Migrations completed!"
echo ""

# Collect static files
echo "[7/8] 📦 Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected!"
echo ""

# Create superuser
echo "[8/8] 👤 Create admin user?"
read -p "Do you want to create an admin user? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    echo "✅ Admin user created!"
else
    echo "⏭️  Skipped admin user creation"
fi
echo ""

# Final summary
echo "======================================="
echo "  ✅ Setup Complete!"
echo "======================================="
echo ""
echo "📝 Next steps:"
echo "1. Ensure your .env file has the SECRET_KEY"
echo "2. Add your GEMINI_API_KEY to .env"
echo "3. Verify core_logic path is correct in .env:"
echo "   CORE_LOGIC_PATH=/path/to/core_logic"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "🌐 Then visit:"
echo "   Home: http://localhost:8000"
echo "   Admin: http://localhost:8000/admin"
echo ""
