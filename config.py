import configparser
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cota.cfg")

def store_in_data_folder(filename: str):
    return os.path.join(os.path.dirname(__file__), "data", filename)

settings = configparser.ConfigParser()
settings.read(CONFIG_FILE)

# GENERAL
APPLICATION_NAME = settings.get("general", "application_name")
DOWNLOADS_DIR = store_in_data_folder(settings.get("general", "downloads_dir"))
LOCAL_UPLOADS_DIR = settings.get("general", "local_uploads_dir")
LOGFILE = store_in_data_folder(settings.get("general", "logfile"))
LOG_LEVEL = settings.get("general", "log_level")

SUPPORTED_EBOOK_FORMATS = ["epub", "pdf"]

# TRACKED BOOKS
TRACKED_MANGAS_FILE = store_in_data_folder(settings.get("tracked_books", "manga"))
TRACKED_LIGHTNOVELS_FILE = store_in_data_folder(settings.get("tracked_books", "lightnovel"))
TRACKED_EBOOKS_FILE = store_in_data_folder(settings.get("tracked_books", "ebook"))

# MEDIA SERVER
MEDIA_SERVER_IP = settings.get("media_server", "ip")
MEDIA_SERVER_PORT = int(settings.get("media_server", "port"))
MEDIA_SERVER_USERNAME = settings.get("media_server", "username")
MEDIA_SERVER_PASSWORD = settings.get("media_server", "password")
MEDIA_SERVER_PATH_TO_MANGAS = settings.get("media_server", "path_to_mangas")
MEDIA_SERVER_PATH_TO_LIGHTNOVELS = settings.get("media_server", "path_to_lightnovels")
MEDIA_SERVER_PATH_TO_EBOOKS = settings.get("media_server", "path_to_ebooks")

# EBOOK READER
EBOOK_READER_IP = settings.get("ebook_reader", "ip")
EBOOK_READER_PORT = int(settings.get("ebook_reader", "port"))
EBOOK_READER_USERNAME = settings.get("ebook_reader", "username")
EBOOK_READER_PKEY_FILE = settings.get("ebook_reader", "pkey")
EBOOK_READER_BASE_PATH = settings.get("ebook_reader", "base_path")