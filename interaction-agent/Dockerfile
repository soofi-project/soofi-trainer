FROM python:3.11.14-slim

WORKDIR /app

# Install dependencies via pyproject.toml
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "src.agent:app", "--host", "0.0.0.0", "--port", "8000"]
