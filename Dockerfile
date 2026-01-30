FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN echo "YANDEX_DISK_OAUTH_TOKEN=y0__xDJo9iEBxiaqj0gj5-YnhYwk7DW3Qf-WbtvpOQdWonq5boEj3ZW1lWR9g" > /app/.env

RUN pip install --upgrade pip && \
    pip install pytest requests python-dotenv pillow

RUN pip install -e .

CMD ["pytest", "tests/", "-v"]