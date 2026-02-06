FROM python:3.11-slim

# ---- basics ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---- system deps (optional, aber sinnvoll) ----
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---- python deps ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- app code ----
COPY src/ ./src/
COPY scripts/ ./scripts/

# ---- runtime config ----
EXPOSE 8000

ENV WEAVIATE_SCHEME=http
ENV WEAVIATE_HOST=weaviate
ENV WEAVIATE_PORT=8080
ENV WEAVIATE_GRPC_PORT=50051
ENV WEAVIATE_COLLECTION=SoofiKnowledge

# ---- start ----
CMD ["python", "-u", "src/vector_mcp/server.py"]
