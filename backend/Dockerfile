FROM python:3.12-slim

# Install system dependencies for WeasyPrint and general build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libglib2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Expose the API port
EXPOSE 8000

# Default command: run the API server
CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
