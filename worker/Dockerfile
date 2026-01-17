# QueryCraft Worker Job
# Cloud Run Job for background data/problem generation

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY backend ./backend
COPY problems ./problems

# Copy worker code
COPY worker ./worker

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run worker
CMD ["python", "-m", "worker.main"]
