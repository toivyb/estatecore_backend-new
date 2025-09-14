# EstateCore Backend Dockerfile

FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Run Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "estatecore_backend.wsgi:app"]