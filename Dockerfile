FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Initialize the SQLite database from CSVs
RUN python src/database.py

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Production server
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:flask_app"]
