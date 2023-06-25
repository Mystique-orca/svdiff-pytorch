# Stage 1: Base image for building dependencies
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Stage 2: Final image for running the application
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy built wheels from the previous stage
COPY --from=builder /wheels /wheels

# Install the application dependencies from wheels
RUN pip install --no-cache-dir --find-links=/wheels -r /app/requirements.txt

# Copy the API code
COPY generate_image_api.py .

# Expose the port
EXPOSE 8000

# Run the API
CMD ["uvicorn", "generate_image_api:app", "--host", "0.0.0.0", "--port", "8000"]
