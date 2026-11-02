FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=FitnessDashboard.settings \
    DJANGO_ENV=docker \
    HOME=/home/django \
    XDG_CACHE_HOME=/home/django/.cache \
    MPLCONFIGDIR=/home/django/.config/matplotlib \
    MPLBACKEND=Agg

WORKDIR /app

# Runtime dependencies for:
# - Matplotlib
# - Pillow
# - WeasyPrint
# - Font rendering
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libcairo2 \
        libffi8 \
        libglib2.0-0 \
        libharfbuzz0b \
        libharfbuzz-subset0 \
        libjpeg62-turbo \
        libopenjp2-7 \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        shared-mime-info \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately to maximize Docker layer caching.
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -r /app/requirements.txt

# Create dedicated non-root user.
RUN addgroup --system django \
    && adduser \
        --system \
        --ingroup django \
        --home /home/django \
        --shell /usr/sbin/nologin \
        django \
    && mkdir -p \
        /home/django/.cache \
        /home/django/.config/matplotlib \
    && chown -R django:django /home/django

# Copy application files with correct ownership.
COPY --chown=django:django . /app

WORKDIR /app/FitnessDashboard

# Generate static files during image build.
RUN DJANGO_SECRET_KEY=dummy-build-secret-key \
    DJANGO_ALLOWED_HOSTS=fitness-dashboard.di-dev.de \
    python manage.py collectstatic --noinput

# Verify Matplotlib initialization during image creation.
RUN python -c "import matplotlib; import matplotlib.pyplot as plt; plt.figure(); plt.close()"

USER django

EXPOSE 8080

# Gunicorn production configuration.
#
# Use synchronous workers to avoid concurrent request handling
# within the same worker process.
#
# Two workers provide limited process-level concurrency.
# Access and error logs are written to container stdout/stderr.
CMD ["gunicorn", \
     "FitnessDashboard.wsgi:application", \
     "--bind", "0.0.0.0:8080", \
     "--worker-class", "sync", \
     "--workers", "2", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--max-requests", "500", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output"]
