FROM python:3.11-slim

# ---- basics ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---- system deps ----
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---- install package ----
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir . \
 && addgroup --system app && adduser --system --ingroup app app

# ---- start ----
USER app

CMD ["python", "-u", "src/knowledge_ingestion/ingest.py"]
