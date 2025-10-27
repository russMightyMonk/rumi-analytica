# ---- Build Stage ----
FROM python:3.11 AS builder

# Set working directory
WORKDIR /app

# Install build tools needed for packages like bcrypt
RUN apt-get update && apt-get install -y build-essential

# Set environment variables (using the modern key=value format)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies into a temporary location
# This creates pre-compiled "wheels" for all packages
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# ---- Final Stage ----
# Start fresh with the small, secure -slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the pre-compiled wheels from the builder stage
COPY --from=builder /app/wheels /wheels/

# Copy the requirements file
COPY requirements.txt .

# Install the packages from the local wheels, avoiding the need to compile
# --no-index prevents reaching out to PyPI, ensuring we only use our local wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]