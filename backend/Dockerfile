# Use official Python 3.12 slim image for a lightweight, secure container
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for compiling Python packages (like psycopg2/PostgreSQL)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies securely bypassing corporate proxy SSL decryption blocks
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org --no-cache-dir -r requirements.txt
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org --no-cache-dir psycopg2-binary  # Mandatory for Cloud SQL PostgreSQL connection

# Copy the rest of the backend source code into the container
COPY . .

# Google Cloud Run dynamically provides the PORT environment variable (default is usually 8080)
ENV PORT=8080

# Expose the port
EXPOSE $PORT

# Command to run the Uvicorn server, binding to 0.0.0.0 and the dynamic Cloud Run PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]