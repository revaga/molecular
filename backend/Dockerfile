# /backend/Dockerfile

# Use Python 3.10 as the base image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt into the container and install the dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend project (services, routes, models, etc.)
COPY . .

# Expose port 8000 for FastAPI (default is 8000)
EXPOSE 8000

# Command to run FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]