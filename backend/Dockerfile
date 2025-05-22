FROM python:3.9-slim

WORKDIR /app

# Install sqlite3 command-line tool
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /data
ENV DATABASE_URL=/data/tasks.db

# Make sure Flask listens on port 8080
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

EXPOSE 8080

# Use gunicorn instead of Flask's development server
CMD gunicorn --bind 0.0.0.0:8080 app:app
