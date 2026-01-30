"""
Набор тестов для эндпоинта создания папки (PUT /v1/disk/resources).
Проверяет успешное создание и обработку основных ошибок валидации.
"""

import pytest
import uuid


class TestCreateFolderResource:
    """Тесты для проверки успешного создания и обработки основных ошибок валидации"""

    def test_create_folder_success(self, api_client, random_path):
        """
        Тест успешного создания новой папки.

        Ожидаемый результат:
            - Код ответа: 201 Created.
            - Папка создается по указанному пути.
            - Последующее удаление созданной папки для очистки окружения.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )
        assert response.status_code == 201, f"Ошибка: {response.text}"
        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    @pytest.mark.parametrize(
        "invalid_path, expected_status, description",
        [
            ("", 400, "Пустой путь должен возвращать 400"),
            (
                "relative/path",
                409,
                "Относительный путь: родительской папки нет -> Conflict",
            ),
            ("/", 409, "Корневая папка уже существует -> Conflict"),
        ],
    )
    def test_create_folder_invalid_path(
        self, api_client, invalid_path, expected_status, description
    ):
        """
        Параметризованный тест для различных некорректных путей.

        Аргументы:
            invalid_path (str): Некорректный тестовый путь.
            expected_status (int): Ожидаемый HTTP-код ответа.
            description (str): Пояснение к тестовому случаю.

        Ожидаемый результат:
            - Сервер возвращает предсказуемый код ошибки (400 или 409).
            - Ответ содержит поясняющее сообщение.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": invalid_path}
        )
        assert (
            response.status_code == expected_status
        ), f"{description}. Путь: '{invalid_path}'. Ответ: {response.text}"

    def test_create_folder_nonexistent_parent(self, api_client):
        """
        Тест попытки создания папки внутри несуществующей родительской директории.

        Ожидаемый результат:
            - Код ответа: 409 Conflict.
            - В теле ответа содержится указание на несуществующий путь.
        """
        non_existent_parent = f"/non_existent_{uuid.uuid4().hex[:8]}"
        nested_path = f"{non_existent_parent}/new_folder"
        response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": nested_path}
        )
        assert (
            response.status_code == 409
        ), f"Ожидалась ошибка 409. Получено: {response.status_code}. Ответ: {response.text}"
        assert (
            "не существует" in response.text
            or "doesn't exists" in response.text.lower()
        )

    def test_create_folder_duplicate_409(self, api_client, random_path):
        """
        Тест попытки создания папки, которая уже существует.

        Шаги:
            1. Создать папку.
            2. Повторно отправить запрос на создание папки по тому же пути.

        Ожидаемый результат:
            - Код ответа на второй запрос: 409 Conflict.
            - Папка удаляется после теста для очистки.
        """
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})
        response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )
        assert response.status_code == 409
        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    def test_create_folder_no_token_401(self):
        """
        Тест попытки создания папки без предоставления OAuth-токена.

        Ожидаемый результат:
            - Код ответа: 401 Unauthorized.
        """
        from requests import Session

        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"
        response = client.put(
            f"{client.base_url}/resources",
            params={"path": f"/test_no_auth_{uuid.uuid4().hex[:8]}"},
        )
        assert response.status_code == 401
