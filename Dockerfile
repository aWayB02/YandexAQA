FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости если нужны
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем все файлы проекта
COPY . .

# Устанавливаем зависимости напрямую из pyproject.toml
RUN pip install --upgrade pip && \
    pip install pytest requests python-dotenv pillow

# Устанавливаем пакет в режиме разработки
RUN pip install -e .

CMD ["pytest", "tests/", "-v"]