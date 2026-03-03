FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN useradd -m appuser
USER appuser

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]