FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN useradd -m appuser
USER appuser

CMD ["python", "-m", "bot.app"]