FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip && \
    pip install pytest requests python-dotenv pillow

RUN pip install -e .

CMD ["pytest", "tests/", "-v"]