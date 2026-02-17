FROM python:3.11-slim

WORKDIR /app

# Install dependencies (pinned in pyproject.toml but installed directly for layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"

# Copy application code
COPY src/ src/

EXPOSE 8000
CMD ["uvicorn", "src.mock_agent:app", "--host", "0.0.0.0", "--port", "8000"]
