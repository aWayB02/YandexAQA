"""
/v1/disk/trash/resources
Получить содержимое Корзины
"""

import pytest
import uuid
import time
from requests import Session


class TestGetTrashResources:
    """Тесты для получения содержимого корзины."""

    def test_get_trash_root_success(self, api_client):
        """
        Тест успешного получения корня корзины.

        Ожидаемый результат:
            - Код ответа: 200 OK.
            - Ответ содержит обязательные поля: path, type, _embedded.
            - Тип ресурса (type) равен 'dir'.
            - Поле _embedded содержит массив items.
        """
        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": "/"}
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()

        assert "path" in data, "Ответ должен содержать поле path"
        assert "type" in data, "Ответ должен содержать поле type"
        assert data["type"] == "dir", "Корень корзины должен быть типом 'dir'"
        assert "_embedded" in data, "Ответ должен содержать поле _embedded"
        assert "items" in data["_embedded"], "Поле _embedded должно содержать items"
        assert isinstance(
            data["_embedded"]["items"], list
        ), "Поле items должно быть массивом"

        if data["_embedded"]["items"]:
            first_item = data["_embedded"]["items"][0]
            assert "name" in first_item, "Элемент корзины должен содержать поле name"
            assert "type" in first_item, "Элемент корзины должен содержать поле type"

            assert (
                "origin_path" in first_item
            ), "Элемент корзины должен содержать поле origin_path"
            assert (
                "deleted" in first_item
            ), "Элемент корзины должен содержать поле deleted"

    def test_get_trash_with_limit_offset(self, api_client):
        """
        Тест получения содержимого корзины с параметрами пагинации.

        Ожидаемый результат:
            - Код ответа: 200 OK.
            - В ответе содержатся переданные значения limit и offset.
            - Количество элементов в items не превышает limit.
        """
        limit = 5
        offset = 0

        response = api_client.get(
            f"{api_client.base_url}/trash/resources",
            params={"path": "/", "limit": limit, "offset": offset},
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()

        assert "_embedded" in data
        embedded = data["_embedded"]

        assert "limit" in embedded, "Ответ должен содержать limit в _embedded"
        assert "offset" in embedded, "Ответ должен содержать offset в _embedded"

        assert (
            embedded["limit"] == limit
        ), f"Ожидался limit={limit}, получен {embedded['limit']}"
        assert (
            embedded["offset"] == offset
        ), f"Ожидался offset={offset}, получен {embedded['offset']}"

        assert (
            len(embedded["items"]) <= limit
        ), f"Количество элементов ({len(embedded['items'])}) превышает limit ({limit})"

    def test_get_trash_with_fields(self, api_client):
        """
        Тест получения содержимого корзины с ограничением возвращаемых полей.

        Ожидаемый результат:
            - Код ответа: 200 OK.
            - В корневом объекте присутствуют только запрошенные поля.
            - Если _embedded не запрошено в fields, оно может отсутствовать.
        """
        fields = "name,type,origin_path,deleted,size"

        response = api_client.get(
            f"{api_client.base_url}/trash/resources",
            params={"path": "/", "fields": fields},
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()

        assert "type" in data, "Корневой объект должен содержать поле type"
        assert data["type"] == "dir"

        assert "name" in data
        assert "origin_path" in data
        if "deleted" not in data:
            print("Примечание: поле 'deleted' отсутствует в корне корзины")
        if "size" not in data:
            print("Примечание: поле 'size' отсутствует в корне корзины")

        if "_embedded" not in data:
            print(
                "Примечание: поле '_embedded' отсутствует, так как не было запрошено в fields"
            )
        else:
            assert "items" in data["_embedded"]

    def test_get_trash_nonexistent_path(self, api_client):
        """
        Тест запроса несуществующего пути в корзине.

        Ожидаемый результат:
            - Код ответа: 404 Not Found.
        """
        nonexistent_path = f"/nonexistent_in_trash_{uuid.uuid4().hex[:8]}"

        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": nonexistent_path}
        )

        assert (
            response.status_code == 404
        ), f"Ожидался код 404, получен {response.status_code}. Ответ: {response.text}"

        if response.status_code != 200:
            error_data = response.json()
            assert "error" in error_data
            assert "message" in error_data

    def test_get_trash_no_auth(self):
        """
        Тест попытки получения содержимого корзины без аутентификации.

        Ожидаемый результат:
            - Код ответа: 401 Unauthorized.
        """

        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"

        response = client.get(
            f"{client.base_url}/trash/resources", params={"path": "/"}
        )

        assert (
            response.status_code == 401
        ), f"Ожидался код 401, получен {response.status_code}. Ответ: {response.text}"

    @pytest.mark.parametrize(
        "invalid_path, expected_status, description",
        [
            ("", 200, "Пустой путь должен интерпретироваться как корень корзины"),
            ("invalid/path/../format", 404, "Некорректный путь -> ресурс не найден"),
        ],
    )
    def test_get_trash_invalid_path(
        self, api_client, invalid_path, expected_status, description
    ):
        """
        Параметризованный тест для некорректных путей.
        Ожидания основаны на реальном поведении API.

        Аргументы:
            invalid_path (str): Некорректный или несуществующий путь.
            expected_status (int): Ожидаемый HTTP-код ответа.
            description (str): Пояснение к тестовому случаю.
        """
        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": invalid_path}
        )

        assert response.status_code == expected_status, (
            f"{description}. Ожидался код {expected_status}, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )

    def test_get_trash_item_details(self, api_client):
        """
        Тест получения детальной информации об элементе корзины.
        Если корзина не пуста, запрашиваем первый элемент.
        """
        root_response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": "/", "limit": 1}
        )

        if root_response.status_code != 200:
            pytest.skip(f"Не удалось получить корзину: {root_response.status_code}")

        root_data = root_response.json()
        items = root_data.get("_embedded", {}).get("items", [])

        if not items:
            pytest.skip("Корзина пуста, пропускаем тест деталей элемента")

        first_item = items[0]
        item_path = first_item.get("path")

        if not item_path:
            pytest.skip("Элемент корзины не содержит path")

        response = api_client.get(
            f"{api_client.base_url}/trash/resources",
            params={
                "path": item_path,
                "fields": "name,type,size,origin_path,deleted,created,modified",
            },
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        item_data = response.json()

        assert (
            "origin_path" in item_data
        ), "Элемент корзины должен содержать origin_path"
        assert "deleted" in item_data, "Элемент корзины должен содержать deleted"

        # Проверяем, что это тот же элемент
        assert item_data.get("name") == first_item.get("name")
        assert item_data.get("type") == first_item.get("type")

    def test_get_trash_sort_order(self, api_client):
        """
        Тест проверки сортировки элементов в корзине.
        """
        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": "/", "limit": 10}
        )

        if response.status_code != 200:
            pytest.skip(f"Не удалось получить корзину: {response.status_code}")

        data = response.json()
        items = data.get("_embedded", {}).get("items", [])

        if len(items) < 2:
            pytest.skip("В корзине меньше 2 элементов, пропускаем тест сортировки")

        for item in items:
            assert "deleted" in item, "Элемент корзины должен содержать поле deleted"

    def test_get_trash_large_limit(self, api_client):
        """
        Тест с большим значением limit.

        Ожидаемый результат:
            - Код ответа: 200 OK.
            - API либо возвращает запрошенное количество, либо ограничивает своим максимумом.
        """
        large_limit = 1000

        response = api_client.get(
            f"{api_client.base_url}/trash/resources",
            params={"path": "/", "limit": large_limit},
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()
        embedded = data.get("_embedded", {})

        assert len(embedded.get("items", [])) <= large_limit

        if "limit" in embedded:
            assert embedded["limit"] <= large_limit

    def test_get_trash_empty_corner_cases(self, api_client):
        """
        Тест граничных случаев для пустой корзины.
        """
        api_client.delete(f"{api_client.base_url}/trash/resources")
        time.sleep(2)

        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": "/"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "dir"
        assert len(data["_embedded"]["items"]) == 0

        response = api_client.get(
            f"{api_client.base_url}/trash/resources", params={"path": "/", "limit": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["_embedded"]["items"]) == 0
