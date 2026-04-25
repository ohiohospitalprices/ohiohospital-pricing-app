# Dockerfile for Hospital Pricing API
# Production-ready containerized deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/hospital_pricing.db \
    DATA_DIR=/app/hospital_data \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY hospital_pricing.zip .
COPY index.html .
COPY *.jpg .
COPY *.png .

# Create data directories
RUN mkdir -p /app/data /app/hospital_data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]

# Expose port
EXPOSE 5000
