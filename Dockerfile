FROM python:3.11-slim

# Install dependencies (ffmpeg, supervisor, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg imagemagick supervisor curl && \
    rm -rf /var/lib/apt/lists/*

# Create app and supervisor log directories
RUN mkdir -p /var/log/supervisor /app

# Set working directory and copy files
WORKDIR /app
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose FastAPI port
EXPOSE 8000

# Start Supervisor to run FastAPI + Celery
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
