import os
import pytest
import requests
from dotenv import load_dotenv
import uuid
import time

load_dotenv()


@pytest.fixture(scope="session")
def api_token():
    """Фикстура для загрузки OAuth-токена."""
    token = os.getenv("YANDEX_DISK_OAUTH_TOKEN")
    return token


@pytest.fixture(scope="session")
def api_client(api_token):
    """Фикстура для создания HTTP-клиента с общими заголовками."""
    headers = {
        "Authorization": f"OAuth {api_token}",
        "Content-Type": "application/json",
    }
    session = requests.Session()
    session.headers.update(headers)
    session.base_url = "https://cloud-api.yandex.net/v1/disk"
    return session


@pytest.fixture
def random_path():
    """Фикстура, возвращающая путь к уникальной тестовой папке."""
    import uuid

    return f"/test_folder_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_file_path(
    api_client,
):
    """
    Фикстура создает тестовый файл для проверки скачивания.
    Возвращает путь к созданному файлу.
    Удаляет файл после завершения теста.
    """
    import tempfile
    import os

    file_name = f"test_file_{uuid.uuid4().hex[:8]}.txt"
    file_path = f"/{file_name}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write("Тестовое содержимое файла для скачивания\n" * 10)
        temp_file_path = tmp.name

    try:
        upload_response = api_client.get(
            f"{api_client.base_url}/resources/upload",
            params={"path": file_path, "overwrite": "true"},
        )

        if upload_response.status_code != 200:
            pytest.skip(f"Не удалось получить URL для загрузки: {upload_response.text}")

        upload_url = upload_response.json()["href"]

        with open(temp_file_path, "rb") as file_content:
            put_response = requests.put(upload_url, files={"file": file_content})

        if put_response.status_code not in [201, 202]:
            pytest.skip(f"Не удалось загрузить тестовый файл: {put_response.text}")

        yield file_path

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        try:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": file_path}
            )
        except:
            pass


@pytest.fixture
def random_file_path():
    """
    Фикстура возвращает случайный путь к файлу для тестирования.
    Не создает файл физически.
    """
    return f"/test_file_{uuid.uuid4().hex[:8]}.txt"


@pytest.fixture
def test_image_file_path(api_client):
    """
    Фикстура создает тестовое изображение для проверки работы превью.
    Возвращает путь к созданному JPG/PNG файлу.
    """
    import tempfile
    from PIL import Image
    import os

    file_name = f"test_image_{uuid.uuid4().hex[:8]}.jpg"
    file_path = f"/{file_name}"

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        img = Image.new("RGB", (100, 100), color="red")
        img.save(tmp.name, "JPEG")
        temp_file_path = tmp.name

    try:
        upload_response = api_client.get(
            f"{api_client.base_url}/resources/upload",
            params={"path": file_path, "overwrite": "true"},
        )

        if upload_response.status_code != 200:
            pytest.skip(f"Не удалось получить URL для загрузки изображения")

        upload_url = upload_response.json()["href"]

        with open(temp_file_path, "rb") as file_content:
            put_response = requests.put(upload_url, files={"file": file_content})

        if put_response.status_code not in [201, 202]:
            pytest.skip(f"Не удалось загрузить тестовое изображение")

        yield file_path

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        try:
            api_client.delete(
                f"{api_client.base_url}/resources", params={"path": file_path}
            )
        except:
            pass


@pytest.fixture
def folder_with_content(api_client, random_path):
    """
    Фикстура создает папку с несколькими тестовыми файлами для проверки
    пагинации и работы с _embedded.
    """
    api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

    for i in range(3):
        file_path = f"{random_path}/test_file_{i}.txt"
        upload_response = api_client.get(
            f"{api_client.base_url}/resources/upload",
            params={"path": file_path, "overwrite": "true"},
        )
        if upload_response.status_code == 200:
            upload_url = upload_response.json()["href"]
            requests.put(upload_url, data=f"Content of file {i}")

    yield random_path
    api_client.delete(f"{api_client.base_url}/resources", params={"path": random_path})


@pytest.fixture
def folder_with_content(api_client, random_path):
    """
    Фикстура создает папку с несколькими тестовыми файлами для проверки
    рекурсивного копирования папок.
    """
    api_client.put(f"{api_client.base_url}/resources", params={"path": random_path})

    for i in range(2):
        file_path = f"{random_path}/test_file_{i}.txt"
        upload_response = api_client.get(
            f"{api_client.base_url}/resources/upload",
            params={"path": file_path, "overwrite": "true"},
        )
        if upload_response.status_code == 200:
            upload_url = upload_response.json()["href"]
            requests.put(upload_url, data=f"Content of file {i}")

    yield random_path

    api_client.delete(f"{api_client.base_url}/resources", params={"path": random_path})


@pytest.fixture
def file_in_trash(api_client, test_file_path):
    """
    Фикстура создает файл и перемещает его в корзину.
    Возвращает путь к файлу (исходный путь используется для доступа к ресурсу в корзине).
    """
    delete_response = api_client.delete(
        f"{api_client.base_url}/resources", params={"path": test_file_path}
    )

    if delete_response.status_code == 202:
        time.sleep(2)

    yield test_file_path


@pytest.fixture
def published_file_path(api_client, test_file_path):
    """
    Фикстура создает опубликованный файл для тестирования отмены публикации.
    Возвращает путь к опубликованному файлу.
    """
    publish_response = api_client.put(
        f"{api_client.base_url}/resources/publish",
        params={"path": test_file_path},
        json={"public_settings": {}},
    )

    if publish_response.status_code not in [200, 201, 202]:
        pytest.skip(
            f"Не удалось опубликовать файл для теста отмены публикации: {publish_response.status_code}"
        )

    time.sleep(4)

    check_response = api_client.get(
        f"{api_client.base_url}/resources",
        params={"path": test_file_path, "fields": "public_url"},
    )

    is_published = (
        check_response.status_code == 200
        and check_response.json().get("public_url") is not None
    )

    if not is_published:
        pytest.skip(f"Файл не опубликовался после запроса: {check_response.text}")

    yield test_file_path

    try:
        final_check = api_client.get(
            f"{api_client.base_url}/resources",
            params={"path": test_file_path, "fields": "public_url"},
        )

        if final_check.status_code == 200 and final_check.json().get("public_url"):
            api_client.delete(
                f"{api_client.base_url}/resources/unpublish",
                params={"path": test_file_path},
            )
    except:
        pass
