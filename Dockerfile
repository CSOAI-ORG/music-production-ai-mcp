FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml .
COPY server.py .
COPY src/ ./src/ 2>/dev/null || true

RUN pip install --no-cache-dir mcp httpx pydantic

EXPOSE 8000

CMD ["python", "server.py"]
