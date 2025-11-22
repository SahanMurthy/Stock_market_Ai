# setup.ps1 - Fixed for Windows & Separate Core Logic

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  Stock Market Analysis Setup" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-Not (Test-Path "requirements.txt")) {
    Write-Host "ERROR: requirements.txt not found!" -ForegroundColor Red
    Write-Host "Please run this script from the Stock_market_frontend directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Install dependencies
Write-Host "[1/7] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Generate SECRET_KEY
Write-Host "[2/7] Generating SECRET_KEY..." -ForegroundColor Yellow
$secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
Write-Host "Generated SECRET_KEY:" -ForegroundColor Cyan
Write-Host $secretKey -ForegroundColor White
Write-Host ""
Write-Host "ACTION REQUIRED: Copy the key above and add it to your .env file" -ForegroundColor Yellow
Write-Host "Format: SECRET_KEY=$secretKey" -ForegroundColor Gray
Read-Host "Press Enter when done"
Write-Host ""

# Create directories
Write-Host "[3/7] Creating directories..." -ForegroundColor Yellow
$directories = @(
    "web/templates",
    "web/static/css",
    "web/static/js",
    "locale",
    "media",
    "staticfiles"
)

foreach ($dir in $directories) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "Directories created!" -ForegroundColor Green
Write-Host ""

# Check for manage.py
Write-Host "[4/7] Checking Django setup..." -ForegroundColor Yellow
if (-Not (Test-Path "manage.py")) {
    Write-Host "ERROR: manage.py not found!" -ForegroundColor Red
    Write-Host "Creating manage.py..." -ForegroundColor Yellow

    $managePyContent = @"
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
"@

    $managePyContent | Out-File -FilePath "manage.py" -Encoding utf8
    Write-Host "manage.py created!" -ForegroundColor Green
}
Write-Host "Django setup verified!" -ForegroundColor Green
Write-Host ""

# Django migrations
Write-Host "[5/7] Running Django migrations..." -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: makemigrations had issues" -ForegroundColor Yellow
}

python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to run migrations" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}
Write-Host "Migrations completed!" -ForegroundColor Green
Write-Host ""

# Collect static files
Write-Host "[6/7] Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput --clear
Write-Host "Static files collected!" -ForegroundColor Green
Write-Host ""

# Create superuser
Write-Host "[7/7] Creating admin user..." -ForegroundColor Yellow
Write-Host "You will be prompted to enter username, email, and password" -ForegroundColor Cyan
python manage.py createsuperuser
Write-Host ""

# Final summary
Write-Host "=======================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Ensure your .env file has the SECRET_KEY" -ForegroundColor White
Write-Host "2. Add your GEMINI_API_KEY to .env" -ForegroundColor White
Write-Host "3. Verify core_logic path is correct" -ForegroundColor White
Write-Host ""
Write-Host "To start the development server:" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Then visit: http://localhost:8000" -ForegroundColor Green
Write-Host "Admin panel: http://localhost:8000/admin" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
