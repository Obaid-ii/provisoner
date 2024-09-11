# Use an official Python runtime as a base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app
# Install PostgreSQL dependencies and build tools
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential
# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Define environment variables
ENV IOT_HUB_HOST=iothubdevuae.azure-devices.net
ENV DATABASE_URL=postgresql://postgres:1234@10.3.16.5:5432/postgres


# Expose port 8000 (FastAPI default port)
EXPOSE 8000

# Command to run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
