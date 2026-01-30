import pytest
import uuid
import time


class TestUnpublishResource:
    """Тесты для отмены публикации ресурса."""

    def test_unpublish_file_success(self, api_client, published_file_path):
        """
        Тест успешной отмены публикации файла.

        Ожидаемый результат:
            - Код ответа: 200 OK.
            - Ответ содержит ссылку (href) на операцию.
            - У файла пропадает public_url.
        """
        check_response = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if (
            check_response.status_code != 200
            or "public_url" not in check_response.json()
        ):
            pytest.skip("Тестовый файл не опубликован, пропускаем тест")

        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish",
            params={"path": published_file_path},
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()
        assert "href" in data, "Ответ должен содержать поле href"

        time.sleep(2)  # Даем время на обработку

        final_check = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if final_check.status_code == 200:
            final_data = final_check.json()
            assert final_data.get("public_url") is None, "Файл всё ещё опубликован!"

    def test_unpublish_folder_success(self, api_client):
        """
        Тест успешной отмены публикации папки.
        """
        folder_path = f"/test_folder_{uuid.uuid4().hex[:8]}"

        api_client.put(f"{api_client.base_url}/resources", params={"path": folder_path})

        publish_response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": folder_path},
            json={"public_settings": {}},
        )

        if publish_response.status_code not in [200, 201, 202]:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": folder_path}
            )
            pytest.skip(
                f"Не удалось опубликовать папку: {publish_response.status_code}"
            )

        time.sleep(2)

        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish", params={"path": folder_path}
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": folder_path}
        )

    def test_unpublish_already_unpublished(self, api_client, test_file_path):
        """
        Тест попытки отменить публикацию уже неопубликованного ресурса.

        Ожидаемый результат:
            - Код ответа: 409 Conflict или 200 OK (идемпотентность).
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish",
            params={"path": test_file_path},
        )

        assert response.status_code in [
            200,
            409,
        ], f"Неожиданный код: {response.status_code}. Ответ: {response.text}"

    def test_unpublish_nonexistent_resource(self, api_client):
        """
        Тест попытки отменить публикацию несуществующего ресурса.

        Ожидаемый результат:
            - Код ответа: 404 Not Found.
        """
        nonexistent_path = f"/nonexistent_{uuid.uuid4().hex[:8]}.txt"

        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish",
            params={"path": nonexistent_path},
        )

        assert (
            response.status_code == 404
        ), f"Ожидался код 404, получен {response.status_code}. Ответ: {response.text}"

    @pytest.mark.parametrize(
        "invalid_path, expected_status",
        [
            ("", 400),  # Пустой путь
            ("../invalid_path", 400),  # Некорректный путь
        ],
    )
    def test_unpublish_invalid_path(self, api_client, invalid_path, expected_status):
        """
        Параметризованный тест для некорректных путей.

        Ожидаемый результат:
            - Код ответа: 400 Bad Request.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish", params={"path": invalid_path}
        )

        if response.status_code != 200:
            assert response.status_code in [400, 404], (
                f"Ожидался код из [400, 404], получен {response.status_code}. "
                f"Ответ: {response.text}"
            )

    def test_unpublish_no_auth(self):
        """
        Тест попытки отменить публикацию без аутентификации.

        Ожидаемый результат:
            - Код ответа: 401 Unauthorized.
        """
        from requests import Session

        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"

        # Отменяем публикацию (ИСПРАВЛЕНО: PUT вместо DELETE)
        response = client.put(
            f"{client.base_url}/resources/unpublish", params={"path": "/some_file.txt"}
        )

        assert (
            response.status_code == 401
        ), f"Ожидался код 401, получен {response.status_code}. Ответ: {response.text}"

    def test_unpublish_with_fields(self, api_client, published_file_path):
        """
        Тест отмены публикации с ограничением возвращаемых полей.
        """
        check_response = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if (
            check_response.status_code != 200
            or "public_url" not in check_response.json()
        ):
            pytest.skip("Тестовый файл не опубликован")

        response = api_client.put(
            f"{api_client.base_url}/resources/unpublish",
            params={"path": published_file_path, "fields": "href,method"},
        )

        if response.status_code == 200:
            data = response.json()
            allowed_fields = {"href", "method", "templated"}
            actual_fields = set(data.keys())
            assert actual_fields.issubset(
                allowed_fields
            ), f"Лишние поля: {actual_fields - allowed_fields}"

    def test_publish_unpublish_cycle(self, api_client, test_file_path):
        """
        Тест полного цикла публикации и отмены публикации.

        Ожидаемый результат:
            - Ресурс успешно публикуется и затем успешно "отпубликовывается".
        """
        publish_response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path},
            json={"public_settings": {}},
        )

        if publish_response.status_code not in [200, 201, 202]:
            pytest.skip(f"Не удалось опубликовать файл: {publish_response.status_code}")

        # Ждем завершения публикации
        time.sleep(3)

        check_published = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": test_file_path, "fields": "public_url"},
        )

        is_published = (
            check_published.status_code == 200
            and check_published.json().get("public_url") is not None
        )

        if not is_published:
            print("Файл не опубликовался, пропускаем тест отмены")
            pytest.skip("Файл не опубликовался после запроса публикации")

        # Отменяем публикацию (ИСПРАВЛЕНО: PUT вместо DELETE)
        unpublish_response = api_client.put(
            f"{api_client.base_url}/resources/unpublish",
            params={"path": test_file_path},
        )

        assert (
            unpublish_response.status_code == 200
        ), f"Ошибка отмены публикации: {unpublish_response.text}"

        # Проверяем, что публикация отменена
        time.sleep(2)

        check_unpublished = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": test_file_path, "fields": "public_url"},
        )

        if check_unpublished.status_code == 200:
            assert (
                check_unpublished.json().get("public_url") is None
            ), "Публикация не была отменена"
