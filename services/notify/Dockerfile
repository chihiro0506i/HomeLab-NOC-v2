FROM python:3.12-slim

LABEL maintainer="homelab-noc-v2"
LABEL description="Notify Hub – event aggregation and notification service"

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create non-root user and data directory
RUN groupadd -r notify && useradd -r -g notify notify \
    && mkdir -p /app/data \
    && chown -R notify:notify /app

USER notify

EXPOSE 8090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--log-level", "info"]
