FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/edc_mcp ./edc_mcp

CMD ["python", "-u", "-m", "edc_mcp.main"]