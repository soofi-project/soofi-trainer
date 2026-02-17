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
COPY src/ ./src/
RUN pip install --no-cache-dir .

# ---- runtime config ----
EXPOSE 8000

# ---- start ----
CMD ["python", "-u", "src/vector_mcp/server.py"]
