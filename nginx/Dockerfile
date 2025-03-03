# /backend/Dockerfile

# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Install system dependencies required for PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend project
COPY . .

# Create cache directory for transformers
RUN mkdir -p /root/.cache/huggingface

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]