import logging
import os
import requests

# Токен вашего бота
# OAuth-токен для доступа к Яндекс.Диску
YANDEX_DISK_TOKEN = "y0_AgAAAABUpXbHAADLWwAAAAEQy6c9AACH0JR5c4dPwZNUlQ26-KQXwF_X3g"
YANDEX_DISK_TOKEN = 'y0_AgAAAABUpXbHAAxuzgAAAAEQzafHAACAR_yapPhFLb2sYOkFDgFJsj8y9w'
# URL для загрузки файлов на Яндекс.Диск
YANDEX_DISK_UPLOAD_URL = "https://cloud-api.yandex.net/v1/disk/resources/upload"
YANDEX_DISK_CREATE_FOLDER_URL = "https://cloud-api.yandex.net/v1/disk/resources"

_logger = logging.getLogger()

def create_folder_on_yandex_disk(yandex_path):
    headers = {"Authorization": f"OAuth {YANDEX_DISK_TOKEN}"}
    params = {"path": yandex_path}
    
    # Пытаемся создать папку
    response = requests.put(YANDEX_DISK_CREATE_FOLDER_URL, headers=headers, params=params)
    
    # Если папка уже существует, игнорируем ошибку
    if response.status_code == 201:
        _logger.info(f"Папка {yandex_path} создана.")
    elif response.status_code == 409:
        _logger.info(f"Папка {yandex_path} уже существует.")
    else:
        _logger.warning(f"Ошибка при создании папки {yandex_path}: {response.status_code}")

# Создаем папки по пути
def ensure_directories_exist(yandex_disk_path):
    # Разбиваем путь и создаем каждую часть отдельно
    parts = yandex_disk_path.split("/")
    for i in range(2, len(parts)):  # Пропускаем первые 2 элемента (Telegram/Reports)
        folder_path = "/".join(parts[:i])
        create_folder_on_yandex_disk(folder_path)

# Используем функцию перед загрузкой файла

# Функция для создания пути на Яндекс.Диске и загрузки файла
def upload_to_yandex_disk(file_path, yandex_path):
    headers = {"Authorization": f"OAuth {YANDEX_DISK_TOKEN}"}
    params = {"path": yandex_path, "overwrite": "true"}

    # Получаем URL для загрузки
    response = requests.get(YANDEX_DISK_UPLOAD_URL, headers=headers, params=params)

    if response.status_code == 200:
        href = response.json()["href"]

        # Загружаем файл на Диск
        with open(file_path, "rb") as file:
            upload_response = requests.put(href, files={"file": file})

        if upload_response.status_code == 201:
            _logger.info("Файл успешно загружен на Яндекс.Диск!")
            os.remove(file_path)
        else:
            _logger.warning("Ошибка при загрузке файла на Яндекс.Диск:", upload_response.status_code)
    else:
        _logger.warning("Ошибка при получении URL для загрузки:", response.status_code)


# Функция для формирования пути на основе даты
def get_yandex_disk_path(file_name, root_folder, creation_date):
    year = creation_date.year
    month = creation_date.strftime("%m")
    suffix = file_name.split(".")[1]
    return f"{root_folder}/{year}/{month}/{suffix}/{file_name}"



