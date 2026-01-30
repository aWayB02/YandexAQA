import pytest
import requests


class TestGetDownloadLink:
    """Тесты для получения ссылки на скачивание файла."""

    def test_get_download_link_success(self, api_client, test_file_path):
        """
        Тест успешного получения ссылки на скачивание существующего файла.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources/download", params={"path": test_file_path}
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()
        assert "href" in data, "Ответ должен содержать поле href"
        assert "method" in data, "Ответ должен содержать поле method"
        assert data.get("method") == "GET", "Метод скачивания должен быть GET"

        download_response = requests.get(data["href"], stream=True)
        assert download_response.status_code == 200, "Ссылка для скачивания не работает"
        download_response.close()

    def test_get_download_link_with_fields(self, api_client, test_file_path):
        """
        Тест получения ссылки на скачивание с указанием необязательного параметра fields.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources/download",
            params={"path": test_file_path, "fields": "href,method"},
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"

        data = response.json()
        assert set(data.keys()) == {
            "href",
            "method",
        }
        assert "templated" not in data

    @pytest.mark.parametrize(
        "invalid_path, expected_status",
        [
            ("", 400),
            ("/nonexistent_file.txt", 404),
            (
                "../invalid_path.txt",
                404,
            ),
        ],
    )
    def test_get_download_link_invalid_path(
        self, api_client, invalid_path, expected_status
    ):
        """
        Параметризованный тест получения ссылки для некорректных путей.

        Ожидаемый результат:
            - Сервер возвращает соответствующий код ошибки.
            - Ответ содержит описание проблемы.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources/download", params={"path": invalid_path}
        )

        assert response.status_code == expected_status, (
            f"Ожидался код {expected_status}, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )

    def test_get_download_link_for_folder(self, api_client, random_path):
        """
        Тест получения ссылки на скачивание папки.
        """
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

        response = api_client.get(
            f"{api_client.base_url}/resources/download", params={"path": random_path}
        )

        assert response.status_code == 200, (
            f"Ожидался успешный код 200 для папки. Получено: {response.status_code}. "
            f"Ответ: {response.text}"
        )

        data = response.json()
        assert "href" in data
        assert "download" in data["href"] or "zip" in data["href"]
        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    def test_get_download_link_no_auth(self):
        """
        Тест попытки получения ссылки без аутентификации.
        """
        client = requests.Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"

        response = client.get(
            f"{client.base_url}/resources/download", params={"path": "/some_file.txt"}
        )

        assert (
            response.status_code == 401
        ), f"Ожидался код 401, получен {response.status_code}. Ответ: {response.text}"

    def test_get_download_link_malformed_fields(self, api_client, test_file_path):
        """
        Тест получения ссылки с некорректным форматом параметра fields.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources/download",
            params={"path": test_file_path, "fields": "invalid_field,another_invalid"},
        )
        if response.status_code == 400:
            assert (
                "invalid" in response.text.lower() or "field" in response.text.lower()
            )
        else:
            assert response.status_code == 200
            data = response.json()
            assert "href" in data and "method" in data

    def test_get_download_link_special_characters(self, api_client):
        """
        Тест получения ссылки для файла со специальными символами в имени.
        """
        test_file = "/test_file_with_spaces and (special).txt"

        response = api_client.get(
            f"{api_client.base_url}/resources/download", params={"path": test_file}
        )

        assert response.status_code != 400
        assert response.status_code in [200, 404]
