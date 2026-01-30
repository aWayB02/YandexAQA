import pytest
import uuid
import time
from requests import Session


class TestEmptyTrash:
    """Тесты для очистки корзины."""

    def test_empty_trash_completely_success(self, api_client):
        """
        Тест успешной полной очистки корзины (без указания path).
        """
        response = api_client.delete(f"{api_client.base_url}/trash/resources")

        assert response.status_code in [204, 202]

        if response.status_code == 202:
            data = response.json()
            assert "href" in data
            assert "operation" in data["href"] or data.get("templated") is True

        time.sleep(2)

    def test_empty_trash_completely_force_async(self, api_client):
        """
        Тест принудительной асинхронной полной очистки корзины.
        """
        # Ждем, чтобы избежать ошибки 423
        time.sleep(2)

        response = api_client.delete(
            f"{api_client.base_url}/trash/resources", params={"force_async": "true"}
        )

        if response.status_code == 423:
            pytest.skip("Корзина заблокирована, пропускаем тест")

        if response.status_code == 202:
            data = response.json()
            assert "href" in data
            assert "operation" in data["href"] or data.get("templated") is True

        elif response.status_code == 204:
            print("API проигнорировал force_async и выполнил операцию синхронно")
        else:
            pytest.fail(
                f"Неожиданный код: {response.status_code}. Ответ: {response.text}"
            )

    def test_empty_trash_with_fields(self, api_client):
        """
        Тест полной очистки корзины с ограничением возвращаемых полей.
        """
        # Ждем, чтобы избежать ошибки 423
        time.sleep(2)

        response = api_client.delete(
            f"{api_client.base_url}/trash/resources", params={"fields": "href,method"}
        )

        if response.status_code == 423:
            pytest.skip("Корзина заблокирована, пропускаем тест")

        assert response.status_code in [204, 202], f"Ошибка: {response.text}"

        if response.status_code == 202:
            data = response.json()
            allowed_fields = {"href", "method", "templated"}
            actual_fields = set(data.keys())
            assert actual_fields.issubset(
                allowed_fields
            ), f"Лишние поля: {actual_fields - allowed_fields}"

    def test_delete_nonexistent_item_from_trash(self, api_client):
        """
        Тест удаления несуществующего ресурса из корзины.
        """
        time.sleep(2)

        nonexistent_path = f"/nonexistent_in_trash_{uuid.uuid4().hex[:8]}.txt"
        response = api_client.delete(
            f"{api_client.base_url}/trash/resources", params={"path": nonexistent_path}
        )

        assert (
            response.status_code == 404
        ), f"Ожидался код 404, получен {response.status_code}. Ответ: {response.text}"

    def test_empty_trash_no_auth(self):
        """
        Тест попытки очистки корзины без аутентификации.
        """

        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"

        response = client.delete(f"{client.base_url}/trash/resources")

        assert (
            response.status_code == 401
        ), f"Ожидался код 401, получен {response.status_code}. Ответ: {response.text}"

    def test_empty_trash_root_path(self, api_client):
        """
        Тест очистки корзины с указанием корневого пути (path=/).
        """
        # Ждем, чтобы избежать ошибки 423
        time.sleep(2)

        response = api_client.delete(
            f"{api_client.base_url}/trash/resources", params={"path": "/"}
        )

        assert response.status_code in [204, 202], f"Ошибка: {response.text}"

    @pytest.mark.parametrize(
        "invalid_async_param",
        [
            "invalid_value", 
            "123",
            "",
        ],
    )
    def test_empty_trash_invalid_async_param(self, api_client, invalid_async_param):
        """
        Тест с некорректным значением параметра force_async.
        """
        time.sleep(5)

        response = api_client.delete(
            f"{api_client.base_url}/trash/resources",
            params={"force_async": invalid_async_param},
        )

        if response.status_code == 423:
            pytest.skip("Корзина заблокирована, пропускаем тест")

        if response.status_code not in [204, 202]:
            assert response.status_code == 400

    def test_empty_trash_async_operation_status(self, api_client):
        """
        Тест проверки статуса асинхронной операции очистки корзины.
        """
        time.sleep(2)

        response = api_client.delete(
            f"{api_client.base_url}/trash/resources", params={"force_async": "true"}
        )

        if response.status_code == 202:
            data = response.json()
            operation_url = data["href"]

            if operation_url.startswith("http"):
                op_response = api_client.get(operation_url)
                assert op_response.status_code in [
                    200,
                    201,
                ]
            else:
                op_response = api_client.get(f"{api_client.base_url}{operation_url}")
                assert op_response.status_code in [
                    200,
                    201,
                ]

    def test_consecutive_empty_trash_requests(self, api_client):
        """
        Тест последовательных запросов на очистку уже пустой корзины.
        """
        # Ждем, чтобы избежать ошибки 423
        time.sleep(2)

        response1 = api_client.delete(f"{api_client.base_url}/trash/resources")
        assert response1.status_code in [204, 202]

        if response1.status_code == 202:
            time.sleep(3)

        response2 = api_client.delete(f"{api_client.base_url}/trash/resources")
        assert response2.status_code in [
            204,
            202,
        ]
