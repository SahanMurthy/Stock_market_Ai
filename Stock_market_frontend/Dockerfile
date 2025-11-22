# Dockerfile - Fixed for separate core_logic

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . /app/

# Note: core_logic will be mounted as volume in docker-compose.yml
# Create directory for it
RUN mkdir -p /app/core_logic

# Create other directories
RUN mkdir -p /app/staticfiles /app/media

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "\
    echo '🔄 Waiting for database...' && \
    while ! nc -z db 5432; do sleep 1; done && \
    echo '✅ Database ready!' && \
    echo '🗄️  Running migrations...' && \
    python manage.py makemigrations --noinput && \
    python manage.py migrate --noinput && \
    echo '📦 Collecting static files...' && \
    python manage.py collectstatic --noinput --clear && \
    echo '🚀 Starting server at http://localhost:8000' && \
    python manage.py runserver 0.0.0.0:8000"]
