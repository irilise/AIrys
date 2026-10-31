# Python 3.11+ slim image with common dependencies
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (chromaDB needs these on some platforms)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    pkg-config \
    g++ \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY config/ ./config/

# Expose the API port
EXPOSE 7860

CMD ["python", "backend/server.py"]
