FROM python:3.11.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["python", "-m", "huggingface_mcp.server"]
