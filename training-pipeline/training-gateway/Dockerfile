FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Data directory for SQLite database
RUN mkdir -p /data
VOLUME /data

EXPOSE 8000

ENV TRAINING_DB_PATH=/data/training.db

CMD ["python", "-u", "src/training_gateway/server.py"]
