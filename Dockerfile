FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pages/ pages/
COPY tests/ tests/

ENV PYTHONUNBUFFERED=1

CMD ["pytest", "tests/", "-v", "-s", "--log-cli-level=INFO", "--tb=short"]
