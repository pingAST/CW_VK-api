from YandexDisk import upYandexDisk
from VK import VKPhotosDownloader

vk_access_token = input("Введите VK токен: ")
yx_access_token = input("Введите токен Яндекса: ")
vk_user_id = input("Введите ID пользователя VK, у которого нужно скачать фотографии: ")

yandex_disk = upYandexDisk(yx_access_token)
yandex_disk.create_folder()

folder_name = yandex_disk.get_folder_name()
vk_downloader = VKPhotosDownloader(vk_access_token, vk_user_id, yx_access_token, folder_name)
photos = vk_downloader.get_photos()
vk_downloader.vk_out_photos_info_to_json(photos)

success_files, error_files = vk_downloader.upload_photos_to_yandex_disk(photos)
output_data = {'success_files': success_files, 'error_files': error_files}
vk_downloader.output_to_json(output_data)



