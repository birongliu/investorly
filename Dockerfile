# Use a Python image
FROM python:3.13-slim

# Avoid buffering and enable pip optimizations
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set workdir inside container
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the project
COPY . /app

# Default command (overridden by docker-compose)
CMD ["python", "-V"]
