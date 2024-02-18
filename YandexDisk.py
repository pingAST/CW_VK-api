import requests

class upYandexDisk:
    def __init__(self, access_token):
        self.access_token = access_token
        self.folder_name = None

    def upload_file(self, file_url, file_path):
        headers = {
            'Authorization': f'OAuth {self.access_token}'
        }
        params = {
            'path': file_path,
            'url': file_url
        }
        response = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload', params=params, headers=headers)
        response.raise_for_status()

    def create_folder(self, input_func=input):
        folder_name = input_func("Введите название новой папки: ")
        self.folder_name = folder_name
        headers = {
            'Authorization': f'OAuth {self.access_token}'
        }
        params = {
            'path': folder_name
        }
        response = requests.put('https://cloud-api.yandex.net/v1/disk/resources', params=params, headers=headers)

        if response.status_code == 409:
            print("Папка уже существует. Пожалуйста, введите другое имя папки.")
            self.create_folder(input_func)  # Рекурсивный вызов для создания новой папки с новым именем
        elif response.status_code != 201:
            raise Exception(f"Ошибка при создании папки: {response.json()}")

    def get_folder_name(self):
        return self.folder_name