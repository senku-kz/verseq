FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run migrations then start the server.
# 'alembic upgrade head' works for both SQLite and PostgreSQL.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
