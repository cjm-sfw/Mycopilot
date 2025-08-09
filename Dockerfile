# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose ports for FastAPI (8000) and Gradio (7860)
EXPOSE 8000
EXPOSE 7860

# Command to run the application
CMD ["sh", "-c", "redis-server --daemonize yes && uvicorn backend.main:app --host 0.0.0.0 --port 8000 & python frontend/app.py"]
