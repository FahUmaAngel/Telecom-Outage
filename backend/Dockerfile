FROM python:3.11-slim

WORKDIR /app

# Install system packages needed for some python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files
COPY backend/requirements.txt ./backend/
COPY scrapers/requirements.txt ./scrapers/

# Install python dependencies from both backend and scrapers 
# since the FastAPI backend orchestrates the scrapers in its lifespan
RUN pip install --no-cache-dir -r backend/requirements.txt -r scrapers/requirements.txt

# Copy all source code (since backend imports from scrapers)
COPY . .

# Set PYTHONPATH so absolute imports work if necessary
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app via uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
