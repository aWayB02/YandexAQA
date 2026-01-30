import pytest
from requests import Session


class TestGetResourceMetadata:
    """Тесты для получения метаинформации о ресурсе."""

    def test_get_file_metadata_success(self, api_client, test_file_path):
        """
        Тест успешного получения метаданных существующего файла.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": test_file_path}
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"
        data = response.json()
        assert data["type"] == "file"
        assert data["path"] == f"disk:{test_file_path}"
        assert "name" in data

    def test_get_folder_metadata_success(self, api_client, random_path):
        """
        Тест успешного получения метаданных существующей папки.
        """
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

        assert response.status_code == 200, f"Ошибка: {response.text}"
        data = response.json()
        assert data["type"] == "dir"

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    def test_get_folder_metadata_with_embedded(
        self, api_client, random_path, test_file_path
    ):
        """
        Тест получения метаданных папки с проверкой содержимого (_embedded).
        """
        # Создаем папку
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

        assert response.status_code == 200
        data = response.json()
        assert "_embedded" in data
        assert "items" in data["_embedded"]

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    @pytest.mark.parametrize(
        "fields, expected_field_count",
        [
            ("name,type,size", 3),
            ("path,modified", 2),
        ],
    )
    def test_get_metadata_with_fields(
        self, api_client, test_file_path, fields, expected_field_count
    ):
        """
        Параметризованный тест с параметром fields.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": test_file_path, "fields": fields},
        )

        assert response.status_code == 200
        data = response.json()
        for field in fields.split(","):
            assert field in data

    @pytest.mark.parametrize(
        "limit, offset",
        [
            (1, 0),
            (2, 1),
        ],
    )
    def test_get_metadata_with_limit_offset(
        self, api_client, random_path, limit, offset
    ):
        """
        Тест работы пагинации через limit и offset для папки с содержимым.
        """
        api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

        response = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": random_path, "limit": limit, "offset": offset},
        )

        assert response.status_code == 200
        data = response.json()
        if "_embedded" in data:
            assert data["_embedded"]["limit"] == limit
            assert data["_embedded"]["offset"] == offset
            assert len(data["_embedded"]["items"]) <= limit

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

    def test_get_metadata_with_preview_params(self, api_client, test_file_path):
        """
        Тест работы параметров превью (preview_crop, preview_size).
        """
        response = api_client.get(
            f"{api_client.base_url}/resources",
            params={
                "path": test_file_path,
                "preview_size": "150x150",
                "preview_crop": "true",
            },
        )

        assert response.status_code == 200
        data = response.json()
        if "preview" in data:
            assert data["preview"].startswith("https://")

    @pytest.mark.parametrize(
        "invalid_path, expected_status",
        [
            ("", 400), 
            ("/nonexistent_folder", 404),
            (
                "../invalid_path",
                404,
            ),
        ],
    )
    def test_get_metadata_invalid_path(self, api_client, invalid_path, expected_status):
        """
        Параметризованный тест для некорректных путей.

        Аргументы:
            invalid_path (str): Некорректный или несуществующий путь.
            expected_status (int): Ожидаемый HTTP-код ошибки.

        Ожидаемый результат:
            - Сервер возвращает соответствующий код ошибки.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": invalid_path}
        )

        assert response.status_code == expected_status, (
            f"Ожидался код {expected_status}, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )

    def test_get_metadata_no_auth(self):
        """
        Тест попытки получения метаданных без аутентификации.
        """
        client = Session()
        client.base_url = "https://cloud-api.yandex.net/v1/disk"
        response = client.get(f"{client.base_url}/resources", params={"path": "/"})

        assert response.status_code == 401

    def test_get_metadata_root_folder(self, api_client):
        """
        Тест получения метаданных корневой папки Диска.
        """
        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": "/"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "dir"
        assert "_embedded" in data
        assert "items" in data["_embedded"]

    def test_get_metadata_special_file(self, api_client):
        """
        Тест получения метаданных для файла со специальными символами.
        """
        special_path = "/test file with spaces & special?chars=1.txt"
        response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": special_path}
        )

        assert response.status_code in [200, 404]
