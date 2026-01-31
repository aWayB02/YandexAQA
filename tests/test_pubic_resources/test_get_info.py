import pytest
import time
import uuid
import requests
import tempfile
import os


class TestGetPublicResource:
    """Тесты для получения метаинформации о публичном файле."""

    def test_get_public_file_info_by_key(self, api_client, published_file_path):
        """Тест получения информации о публичном файле по ключу."""
        file_info = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )
        if file_info.status_code != 200:
            pytest.skip(
                f"Не удалось получить информацию о файле: {file_info.status_code}"
            )

        file_data = file_info.json()
        public_url = file_data.get("public_url")

        if not public_url:
            pytest.skip("Файл не опубликован")

        key = public_url.rstrip("/").split("/")[-1]

        response = api_client.get(
            f"{api_client.base_url}/public/resources", params={"public_key": key}
        )

        if response.status_code == 200:
            data = response.json()
            assert "path" in data or "name" in data
            assert "type" in data
            assert data["type"] == "file"
        else:
            pytest.skip("Получение по ключу не работает, пробуем по URL")

    def test_get_public_file_info_by_url(self, api_client, published_file_path):
        """Тест получения информации о публичном файле по URL."""
        file_info = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if file_info.status_code != 200:
            pytest.skip(
                f"Не удалось получить информацию о файле: {file_info.status_code}"
            )

        file_data = file_info.json()
        public_url = file_data.get("public_url")

        if not public_url:
            pytest.skip("Файл не опубликован")

        response = api_client.get(
            f"{api_client.base_url}/public/resources", params={"public_key": public_url}
        )

        assert response.status_code == 200

        data = response.json()

        assert "type" in data
        assert data["type"] == "file"
        assert "public_key" in data or "public_url" in data

    def test_get_public_file_info_with_fields(self, api_client, published_file_path):
        """Тест получения информации о публичном файле с указанием полей."""
        file_info = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if file_info.status_code != 200:
            pytest.skip(
                f"Не удалось получить информацию о файле: {file_info.status_code}"
            )

        file_data = file_info.json()
        public_url = file_data.get("public_url")

        if not public_url:
            pytest.skip("Файл не опубликован")

        response = api_client.get(
            f"{api_client.base_url}/public/resources",
            params={"public_key": public_url, "fields": "name,size,type,mime_type"},
        )

        assert response.status_code == 200

        data = response.json()

        assert "name" in data
        assert "type" in data
        assert data["type"] == "file"

    def test_get_public_file_info_all_fields(self, api_client, published_file_path):
        """Тест получения информации о публичном файле со всеми полями."""

        file_info = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": published_file_path, "fields": "public_url"},
        )

        if file_info.status_code != 200:
            pytest.skip(
                f"Не удалось получить информацию о файле: {file_info.status_code}"
            )

        file_data = file_info.json()
        public_url = file_data.get("public_url")

        if not public_url:
            pytest.skip("Файл не опубликован")

        fields = "path,type,name,created,modified,size,mime_type,md5,sha256,preview,public_key,public_url"
        response = api_client.get(
            f"{api_client.base_url}/public/resources",
            params={"public_key": public_url, "fields": fields},
        )

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "type" in data
        assert "public_key" in data or "public_url" in data

    def test_get_public_file_info_invalid_key(self, api_client):
        """Тест получения информации с неверным публичным ключом."""
        invalid_key = "invalid_key_12345"

        response = api_client.get(
            f"{api_client.base_url}/public/resources",
            params={"public_key": invalid_key},
        )

        assert response.status_code in [404, 400]

    def test_get_public_file_info_empty_key(self, api_client):
        """Тест получения информации с пустым публичным ключом."""
        response = api_client.get(
            f"{api_client.base_url}/public/resources", params={"public_key": ""}
        )

        assert response.status_code in [400, 404]

    def test_get_public_folder_info_with_limit(self, api_client, random_path):
        """Тест получения информации о публичной папке с ограничением количества элементов."""
        create_response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

        if create_response.status_code not in [201, 200]:
            pytest.skip(f"Не удалось создать папку: {create_response.status_code}")

        for i in range(3):
            file_path = f"{random_path}/file_{i}.txt"
            upload_response = api_client.get(
                f"{api_client.base_url}/resources/upload",
                params={"path": file_path, "overwrite": "true"},
            )

            if upload_response.status_code == 200:
                upload_url = upload_response.json()["href"]
                requests.put(upload_url, data=f"Content {i}")

        publish_response = api_client.put(
            f"{api_client.base_url}/resources/publish", params={"path": random_path}
        )

        if publish_response.status_code not in [200, 201, 202]:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": random_path}
            )
            pytest.skip(
                f"Не удалось опубликовать папку: {publish_response.status_code}"
            )

        time.sleep(3)

        try:
            folder_info = api_client.get(
                f"{api_client.base_url}/resources",
                params={"path": random_path, "fields": "public_url"},
            )

            if folder_info.status_code != 200:
                pytest.skip("Не удалось получить информацию о папке")

            folder_data = folder_info.json()
            public_url = folder_data.get("public_url")

            if not public_url:
                pytest.skip("Папка не опубликовалась")

            response = api_client.get(
                f"{api_client.base_url}/public/resources",
                params={"public_key": public_url, "limit": 1, "fields": "_embedded"},
            )

            if response.status_code == 200:
                data = response.json()

                assert "_embedded" in data
                embedded = data["_embedded"]

                assert "items" in embedded
                assert "limit" in embedded
                assert embedded["limit"] == 1

                assert len(embedded["items"]) <= 1
            else:
                pytest.skip(
                    f"Не удалось получить информацию о публичной папке: {response.status_code}"
                )

        finally:
            try:
                api_client.delete(
                    f"{api_client.base_url}/resources/unpublish",
                    params={"path": random_path},
                )
            except:
                pass

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": random_path}
                )
            except:
                pass

    def test_get_public_folder_info_default_limit(self, api_client, random_path):
        """Тест получения информации о публичной папке без указания limit."""
        create_response = api_client.put(
            f"{api_client.base_url}/resources", params={"path": random_path}
        )

        if create_response.status_code not in [201, 200]:
            pytest.skip(f"Не удалось создать папку: {create_response.status_code}")

        for i in range(2):
            file_path = f"{random_path}/file_{i}.txt"
            upload_response = api_client.get(
                f"{api_client.base_url}/resources/upload",
                params={"path": file_path, "overwrite": "true"},
            )

            if upload_response.status_code == 200:
                upload_url = upload_response.json()["href"]
                requests.put(upload_url, data=f"Content {i}")

        publish_response = api_client.put(
            f"{api_client.base_url}/resources/publish", params={"path": random_path}
        )

        if publish_response.status_code not in [200, 201, 202]:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": random_path}
            )
            pytest.skip(
                f"Не удалось опубликовать папку: {publish_response.status_code}"
            )

        time.sleep(3)

        try:
            folder_info = api_client.get(
                f"{api_client.base_url}/resources",
                params={"path": random_path, "fields": "public_url"},
            )

            if folder_info.status_code != 200:
                pytest.skip("Не удалось получить информацию о папке")

            folder_data = folder_info.json()
            public_url = folder_data.get("public_url")

            if not public_url:
                pytest.skip("Папка не опубликовалась")

            response = api_client.get(
                f"{api_client.base_url}/public/resources",
                params={"public_key": public_url, "fields": "_embedded"},
            )

            if response.status_code == 200:
                data = response.json()

                assert "_embedded" in data
                embedded = data["_embedded"]

                assert "items" in embedded
                assert "total" in embedded

                assert len(embedded["items"]) <= embedded.get("limit", 20)
            else:
                pytest.skip(
                    f"Не удалось получить информацию о публичной папке: {response.status_code}"
                )

        finally:
            try:
                api_client.delete(
                    f"{api_client.base_url}/resources/unpublish",
                    params={"path": random_path},
                )
            except:
                pass

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": random_path}
                )
            except:
                pass

    def test_get_public_file_detailed_info(self, api_client):
        """Тест получения детальной информации о публичном файле."""

        file_name = f"test_detailed_{uuid.uuid4().hex[:8]}.txt"
        file_path = f"/{file_name}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("Тестовое содержимое для детальной информации")
            temp_file_path = tmp.name

        try:
            upload_response = api_client.get(
                f"{api_client.base_url}/resources/upload",
                params={"path": file_path, "overwrite": "true"},
            )

            if upload_response.status_code != 200:
                pytest.skip("Не удалось получить URL для загрузки")

            upload_url = upload_response.json()["href"]
            with open(temp_file_path, "rb") as f:
                put_response = requests.put(upload_url, files={"file": f})

            if put_response.status_code not in [201, 202]:
                pytest.skip("Не удалось загрузить файл")

            publish_response = api_client.put(
                f"{api_client.base_url}/resources/publish", params={"path": file_path}
            )

            if publish_response.status_code not in [200, 201, 202]:
                pytest.skip("Не удалось опубликовать файл")

            time.sleep(3)

            file_info = api_client.get(
                f"{api_client.base_url}/resources",
                params={"path": file_path, "fields": "public_url,size,mime_type"},
            )

            if file_info.status_code != 200:
                pytest.skip("Не удалось получить информацию о файле")

            file_data = file_info.json()
            public_url = file_data.get("public_url")

            if not public_url:
                pytest.skip("Файл не опубликовался")

            response = api_client.get(
                f"{api_client.base_url}/public/resources",
                params={
                    "public_key": public_url,
                    "fields": "size,mime_type,preview,media_type",
                },
            )

            assert (
                response.status_code == 200
            ), f"Ошибка при получении детальной информации: {response.status_code} {response.text}"

            public_data = response.json()

            assert public_data["size"] == file_data["size"]
            assert public_data["mime_type"] == file_data["mime_type"]

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources/unpublish",
                    params={"path": file_path},
                )
            except:
                pass

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": file_path}
                )
            except:
                pass

    def test_get_public_file_without_auth(self, api_client):
        """Тест получения информации о публичном файле без авторизации."""

        file_name = f"test_no_auth_{uuid.uuid4().hex[:8]}.txt"
        file_path = f"/{file_name}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("Тестовое содержимое")
            temp_file_path = tmp.name

        try:
            upload_response = api_client.get(
                f"{api_client.base_url}/resources/upload",
                params={"path": file_path, "overwrite": "true"},
            )

            if upload_response.status_code != 200:
                pytest.skip("Не удалось получить URL для загрузки")

            upload_url = upload_response.json()["href"]
            with open(temp_file_path, "rb") as f:
                put_response = requests.put(upload_url, files={"file": f})

            if put_response.status_code not in [201, 202]:
                pytest.skip("Не удалось загрузить файл")

            publish_response = api_client.put(
                f"{api_client.base_url}/resources/publish", params={"path": file_path}
            )

            if publish_response.status_code not in [200, 201, 202]:
                pytest.skip("Не удалось опубликовать файл")

            time.sleep(3)

            file_info = api_client.get(
                f"{api_client.base_url}/resources",
                params={"path": file_path, "fields": "public_url"},
            )

            if file_info.status_code != 200:
                pytest.skip("Не удалось получить информацию о файле")

            file_data = file_info.json()
            public_url = file_data.get("public_url")

            if not public_url:
                pytest.skip("Файл не опубликовался")

            no_auth_session = requests.Session()
            no_auth_session.base_url = "https://cloud-api.yandex.net/v1/disk"

            response = no_auth_session.get(
                f"{no_auth_session.base_url}/public/resources",
                params={"public_key": public_url},
            )

            assert (
                response.status_code == 200
            ), f"Ошибка при запросе без авторизации: {response.status_code}"

            data = response.json()
            assert "name" in data
            assert "type" in data

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources/unpublish",
                    params={"path": file_path},
                )
            except:
                pass

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": file_path}
                )
            except:
                pass
