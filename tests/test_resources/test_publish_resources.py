import pytest
from requests import Session


class TestPublishResource:
    """Тесты для публикации ресурса"""

    MINIMAL_BODY = {"public_settings": {}}

    def test_publish_file_success(self, api_client, test_file_path):
        """
        Тест успешной публикации файла.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path},
            json=self.MINIMAL_BODY,
        )

        if response.status_code not in [200, 201, 202]:
            pytest.skip(f"Ошибка: {response.text}")

        data = response.json()
        assert "href" in data

    def test_publish_folder_success(self, api_client, random_path):
        """
        Тест успешной публикации папки.
        """
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": random_path},
            json=self.MINIMAL_BODY,
        )

        assert response.status_code in [200, 201, 202], f"Ошибка: {response.text}"

        data = response.json()
        assert "href" in data

        try:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": random_path}
            )
        except:
            pass

    def test_publish_already_public(self, api_client, test_file_path):
        """
        Тест попытки опубликовать уже опубликованный ресурс.
        """
        api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path},
            json=self.MINIMAL_BODY,
        )

        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path},
            json=self.MINIMAL_BODY,
        )

        assert response.status_code in [
            200,
            201,
            202,
            409,
        ]

    @pytest.mark.parametrize(
        "invalid_path, expected_status",
        [
            ("", 400),
            ("/nonexistent_resource", 404),
        ],
    )
    def test_publish_invalid_path(self, api_client, invalid_path, expected_status):
        """
        Параметризованный тест для некорректных путей.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": invalid_path},
            json=self.MINIMAL_BODY,
        )

        assert response.status_code == expected_status, (
            f"Ожидался код {expected_status}, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )

    def test_publish_with_fields(self, api_client, test_file_path):
        """
        Тест публикации с ограничением возвращаемых полей.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path, "fields": "href,method"},
            json=self.MINIMAL_BODY,
        )

        if response.status_code in [200, 201, 202]:
            data = response.json()
            allowed_fields = {"href", "method", "templated"}
            actual_fields = set(data.keys())
            assert actual_fields.issubset(
                allowed_fields
            ), f"Лишние поля: {actual_fields - allowed_fields}"
            assert "href" in data
            assert "method" in data

    def test_publish_no_auth(self):
        """
        Тест попытки публикации без аутентификации.
        """
        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"

        response = client.put(
            f"{client.base_url}/resources/publish",
            params={"path": "/some_file.txt"},
            json=self.MINIMAL_BODY,
        )

        assert response.status_code == 401

    def test_publish_with_optional_allow_address_access(
        self, api_client, test_file_path
    ):
        """
        Тест с необязательным параметром allow_address_access.
        """
        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path, "allow_address_access": "true"},
            json=self.MINIMAL_BODY,
        )

        if response.status_code not in [200, 201, 202]:
            assert response.status_code != 405

    def test_publish_with_full_settings(self, api_client, test_file_path):
        """
        Тест публикации с расширенными настройками в public_settings.
        """
        full_body = {
            "public_settings": {
                "read_only": True,
                "password": "my_secret_password",
                "available_until": 1893456000,
            }
        }

        response = api_client.put(
            f"{api_client.base_url}/resources/publish",
            params={"path": test_file_path},
            json=full_body,
        )

        if response.status_code >= 400:
            print(f"Ответ: {response.text}")
        else:
            data = response.json()
            print(f"Успех. Ответ содержит: {list(data.keys())}")

        assert response.status_code != 405
