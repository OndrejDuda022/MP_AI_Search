# ============================================================================
# AI Search API - Dockerfile
# ============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and setup
COPY src/ ./src/
COPY setup.py .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
