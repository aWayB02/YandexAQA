.PHONY: build test tests test-single test-with-coverage shell clean help

# Переменные для настройки
DOCKER_IMAGE = yandexaqa-tests
PYTEST_ARGS = -v --tb=short --color=yes
COV_ARGS = --cov=src --cov-report=term-missing --cov-report=html

# Сборка образа
build:
	docker build -t $(DOCKER_IMAGE) .

# Запуск всех тестов с подробным выводом
test:
	docker run --rm $(DOCKER_IMAGE) pytest $(PYTEST_ARGS) tests/

# Альтернативное название для test (псевдоним)
tests: test

# Запуск конкретного теста/файла
test-single:
	docker run --rm $(DOCKER_IMAGE) pytest $(PYTEST_ARGS) $(FILE)

# Получить shell в контейнере
shell:
	docker run -it --rm --entrypoint=bash $(DOCKER_IMAGE)

# Очистка
clean:
	docker rmi $(DOCKER_IMAGE) || true