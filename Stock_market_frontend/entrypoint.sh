#!/bin/bash
# entrypoint.sh - Simplified setup

set -e

echo "======================================="
echo "  🚀 Stock Market Analysis System"
echo "======================================="
echo ""

# Wait for database
echo "[1/4] 🔄 Waiting for database..."
attempt=0
max_attempts=30
until nc -z db 5432 || [ $attempt -eq $max_attempts ]; do
  attempt=$((attempt+1))
  echo "  Attempt $attempt/$max_attempts..."
  sleep 1
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ Database connection failed!"
  exit 1
fi
echo "✅ Database is ready!"
echo ""

# Generate SECRET_KEY if not set
if [ -z "$SECRET_KEY" ]; then
  echo "[2/4] 🔑 Generating SECRET_KEY..."
  export SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
  echo "⚠️  Add this to your .env file: SECRET_KEY=$SECRET_KEY"
else
  echo "[2/4] ✅ SECRET_KEY found"
fi
echo ""

# Run migrations
echo "[3/4] 🗄️  Running database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
echo "✅ Migrations completed!"
echo ""

# Collect static files
echo "[4/4] 📦 Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected!"
echo ""

echo "======================================="
echo "  ✅ Setup Complete!"
echo "======================================="
echo ""
echo "🌐 Application: http://localhost:8000"
echo "📝 To create superuser, run:"
echo "   docker-compose exec web python manage.py createsuperuser"
echo ""

# Execute the main command
exec "$@"
