# /backend/Dockerfile
# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://user:password@postgres/db

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-pip \
    cmake \
    build-essential \
    pkg-config \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]