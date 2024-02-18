import requests
import json
from datetime import datetime
from tqdm import tqdm
from YandexDisk import upYandexDisk

class VKPhotosDownloader:
    def __init__(self, access_token, user_id, yx_access_token, folder_name):
        self.access_token = access_token
        self.user_id = user_id
        self.yx_access_token = yx_access_token
        self.name_folder = folder_name

    def convert_unixtime_to_readable(self, unix_timestamp):
        return datetime.utcfromtimestamp(unix_timestamp).strftime('%d-%m-%Y_%H-%M-%S')

    def choose_photo_source(self):
        while True:
            source = input("Выберите откуда нужно скачать фотографии (1 - wall(со стены), 2 - profile (профиля)): ")
            if source == '1':
                status_source = 'wall'
                print(f"Выбран источник фотографий: {status_source}")
                return status_source
            elif source == '2':
                status_source = 'profile'
                print(f"Выбран источник фотографий: {status_source}")
                return status_source
            else:
                print("Пожалуйста, выберите '1' для wall или '2' для profile.")

    def get_total_photos_count(self):
        album_id = self.choose_photo_source()

        params = {
            'access_token': self.access_token,
            'owner_id': self.user_id,
            'album_id': album_id,
            'v': '5.131'
        }
        response = requests.get('https://api.vk.com/method/photos.get', params=params)
        data = response.json()

        if 'error' in data:
            raise Exception(f"Error: {data['error']['error_msg']}")

        total_count = data['response']['count']
        return total_count, album_id

    def get_user_choice(self, total_count, default_count=5):
        choice = input(
            f"Всего {total_count} фотографий. Введите количество фотографий для загрузки фотографий на ЯндексДиск. По умолчанию — {default_count}, «all» - вывести все фотографии: ")

        if choice.lower() == 'all':
            count = total_count
        elif choice.isdigit():
            count = int(choice)
            if count < 1:
                print("Ошибка: Введенное число должно быть больше нуля. Установлено значение по умолчанию.")
                count = default_count
            elif count > total_count:
                print(
                    "Ошибка: Введенное число превышает общее количество фотографий. Установлено значение по умолчанию.")
                count = default_count
        elif choice == "":
            print("Предупреждение: Введенное значение равно 0 или пустая строка. Установлено значение по умолчанию.")
            count = default_count
        else:
            print("Ошибка: Введено некорректное значение. Установлено значение по умолчанию.")
            count = default_count

        return count


    def get_photos(self):
        total_count, album_id = self.get_total_photos_count()
        chosen_count = self.get_user_choice(total_count)

        params = {
            'access_token': self.access_token,
            'owner_id': self.user_id,
            'album_id': album_id,
            'extended': 1,
            'photo_sizes': 1,
            'rev': 1,
            'v': '5.131',
            'count': chosen_count
        }
        response = requests.get('https://api.vk.com/method/photos.get', params=params)
        data = response.json()

        if 'error' in data:
            raise Exception(f"Error: {data['error']['error_msg']}")

        photos = data['response']['items']
        total_count = data['response']['count']

        max_size_photos = {
            'count_all': total_count,
            'up_photos': params['count'],
            'photos': []
        }

        for photo in tqdm(photos, desc="Загрузка фотографий из ВК", unit="photo"):
            likes = photo['likes']['count']
            file_name = str(likes)
            max_size_photo = max(photo['sizes'], key=lambda x: x['width'])
            url = max_size_photo['url']
            type = max_size_photo['type']
            date = self.convert_unixtime_to_readable(photo['date'])
            size = {
                'width': max_size_photo['width'],
                'height': max_size_photo['height']
            }
            max_size_photos['photos'].append({
                'likes': likes,
                'file_name': file_name,
                'url': url,
                'type': type,
                'date': date,
                'size': size
            })

        max_size_photos['photos'].sort(key=lambda x: x['likes'], reverse=True)

        # Добавление даты загрузки, если количество лайков одинаково
        prev_likes = None
        counter = 1
        for photo in max_size_photos['photos']:
            if photo['likes'] == prev_likes:
                if photo['date'] == prev_date:
                    file_name_parts = photo['file_name'].split('.')
                    file_name_parts[0] += '_' + photo['date'] + '_' + str(counter)
                    counter += 1
                    photo['file_name'] = '.'.join(file_name_parts)
                else:
                    photo['file_name'] += '_' + photo['date']
            else:
                photo['file_name'] += '_' + photo['date']
            prev_likes = photo['likes']
            prev_date = photo['date']

        return max_size_photos

    def upload_photos_to_yandex_disk(self, photos):
        yandex_disk = upYandexDisk(self.yx_access_token)
        success_files = []
        error_files = []
        for photo in tqdm(photos['photos'], desc="Загрузка фотографий на ЯндексДиск", unit="photo"):
            file_name = photo['file_name']
            url = photo['url']
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    yandex_disk.upload_file(url, f"{self.name_folder}/{file_name}.jpg")
                    success_files.append({
                        'file_name': file_name,
                        'type': photo['type'],
                        'size': str(photo['size']['width']) + 'x' + str(photo['size']['height'])

                    })
                except Exception as e:
                    error_files.append({
                        'file_name': file_name,
                        'error_message': str(e)
                    })
            else:
                error_files.append({
                    'file_name': file_name,
                    'error_message': f"Не удалось загрузить c URL-адреса: {url}"
                })
        print("Операция загрузки фотографий завершена.")
        print(f"Файлы успешно загружены в папку: {self.name_folder}")
        print(f"Дополнительная информация доступна в файле output.json и информация фотографий о VK доступна в файле vk_photos_info.json")
        return success_files, error_files

    def output_to_json(self, data):
        with open('output.json', 'w') as file:
            json.dump(data, file, indent=4)

    def vk_out_photos_info_to_json(self,photos):
        with open('vk_photos_info.json', 'w') as file:
            json.dump(photos, file, indent=4)