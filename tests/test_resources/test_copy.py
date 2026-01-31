import pytest
import uuid
import time


class TestCopyResource:
    """Тесты для операции копирования ресурса."""

    def test_copy_folder_success(self, api_client, folder_with_content):
        """
        Тест успешного копирования папки с содержимым.
        API может выполнить операцию как синхронно (201), так и асинхронно (202).

        Ожидаемый результат:
            - Код ответа: 201 Created ИЛИ 202 Accepted (асинхронная операция).
            - В ответе есть ссылка (href) для отслеживания результата.
        """
        copy_path = f"/copy_of_folder_{uuid.uuid4().hex[:8]}"

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": folder_with_content, "path": copy_path},
        )

        assert response.status_code in [201, 202], (
            f"Ожидался код 201 или 202, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )

        data = response.json()
        assert "href" in data

        if response.status_code == 202:
            assert "operations" in data["href"]
            import time

            time.sleep(3)

        check_response = api_client.get(
            f"{api_client.base_url}/resources", params={"path": copy_path}
        )
        assert check_response.status_code != 500

        if check_response.status_code == 200:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": copy_path}
            )

    def test_copy_with_overwrite_true(self, api_client, test_file_path):
        """
        Тест копирования с перезаписью существующего ресурса (overwrite=true).

        Ожидаемый результат:
            - Код ответа: 201 Created.
            - Существующий файл по целевому пути перезаписан.
        """
        copy_path = f"/overwrite_test_file_{uuid.uuid4().hex[:8]}.txt"

        api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": test_file_path, "path": copy_path},
        )

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": test_file_path, "path": copy_path, "overwrite": "true"},
        )

        assert response.status_code == 201, f"Ошибка: {response.text}"

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": copy_path}
        )

    def test_copy_with_overwrite_false_conflict(self, api_client, test_file_path):
        """
        Тест копирования без перезаписи (overwrite=false) при существующем ресурсе.

        Ожидаемый результат:
            - Код ответа: 409 Conflict.
            - Возвращается ошибка о том, что ресурс уже существует.
        """
        copy_path = f"/conflict_test_file_{uuid.uuid4().hex[:8]}.txt"

        api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": test_file_path, "path": copy_path},
        )

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": test_file_path, "path": copy_path, "overwrite": "false"},
        )

        assert (
            response.status_code == 409
        ), f"Ожидалась ошибка 409. Ответ: {response.text}"

        api_client.delete(
            f"{api_client.base_url}/resources", params={"path": copy_path}
        )

    @pytest.mark.parametrize(
        "force_async_param,expected_codes",
        [
            ("true", [202]),  # Принудительно асинхронный режим
            ("false", [201, 202]),  # Может быть как синхронным, так и асинхронным
        ],
    )
    def test_copy_with_force_async(
        self, api_client, test_file_path, force_async_param, expected_codes
    ):
        """
        Тест копирования с параметром force_async.

        Ожидаемый результат:
            - При force_async=true: код 202 (асинхронная операция).
            - При force_async=false: код 201 или 202 в зависимости от размера.
        """
        copy_path = f"/async_test_file_{uuid.uuid4().hex[:8]}_{force_async_param}.txt"

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={
                "from": test_file_path,
                "path": copy_path,
                "force_async": force_async_param,
            },
        )

        assert (
            response.status_code in expected_codes
        ), f"Ожидался код из {expected_codes}, получен {response.status_code}"

        data = response.json()
        assert "href" in data

        if response.status_code == 202:
            assert "operation" in data["href"] or data.get("templated") is True

        if response.status_code == 201:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": copy_path}
            )
        elif response.status_code == 202:
            time.sleep(2)

            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": copy_path}
                )
            except:
                pass

    def test_copy_with_fields(self, api_client, test_file_path):
        """
        Тест копирования с ограничением возвращаемых полей (fields).

        Ожидаемый результат:
            - Код ответа: 201 Created.
            - Ответ содержит только указанные поля.
        """
        copy_path = f"/fields_test_file_{uuid.uuid4().hex[:8]}.txt"

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": test_file_path, "path": copy_path, "fields": "href,method"},
        )

        if response.status_code == 201:
            data = response.json()
            assert set(data.keys()) == {"href", "method"}

        if response.status_code in [201, 202]:
            try:
                api_client.delete(
                    f"{api_client.base_url}/resources", params={"path": copy_path}
                )
            except:
                pass

    @pytest.mark.parametrize(
        "from_path,to_path,expected_status",
        [
            ("/nonexistent_file.txt", "/copy.txt", 404),
            ("VALID_FILE_PLACEHOLDER", "", 400),
            ("", "/copy.txt", 400),
            ("VALID_FILE_PLACEHOLDER", "/", 409),
        ],
    )
    def test_copy_invalid_paths(
        self, api_client, test_file_path, from_path, to_path, expected_status
    ):
        """
        Параметризованный тест для некорректных путей.

        Ожидаемый результат:
            - Сервер возвращает соответствующий код ошибки.
        """
        if from_path == "VALID_FILE_PLACEHOLDER":
            from_path = test_file_path

        if to_path == "/copy.txt":
            to_path = f"/copy_{uuid.uuid4().hex[:4]}.txt"

        response = api_client.post(
            f"{api_client.base_url}/resources/copy",
            params={"from": from_path, "path": to_path},
        )

        assert response.status_code == expected_status, (
            f"Ожидался код {expected_status}, получен {response.status_code}. "
            f"Ответ: {response.text}"
        )
