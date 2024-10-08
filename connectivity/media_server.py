import paramiko
import traceback
import os

from config import (
    MEDIA_SERVER_IP, MEDIA_SERVER_PORT, MEDIA_SERVER_USERNAME, MEDIA_SERVER_PASSWORD, 
    MEDIA_SERVER_PATH_TO_MANGAS, MEDIA_SERVER_PATH_TO_LIGHTNOVELS, MEDIA_SERVER_PATH_TO_EBOOKS,
    SUPPORTED_EBOOK_FORMATS)
from utils.log import Log

class MediaServer:

    transport = None
    sftp = None

    def connect(self):
        try:
            Log.debug(f"Connecting to media server : {MEDIA_SERVER_USERNAME}@{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}")

            self.transport = paramiko.Transport((MEDIA_SERVER_IP,MEDIA_SERVER_PORT))
            self.transport.connect(username=MEDIA_SERVER_USERNAME, password=MEDIA_SERVER_PASSWORD)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)

            Log.debug("Connection successful")
        except:
            Log.error("Failed to connect to media server", traceback.format_exc())

    def disconnect(self):
        try:
            if self.sftp and self.transport:
                Log.debug(f"Disconnecting from media server : {MEDIA_SERVER_USERNAME}@{MEDIA_SERVER_IP}:{MEDIA_SERVER_PORT}")

                self.sftp = self.sftp.close()
                self.transport = self.transport.close()

                Log.debug("Disconnection successful")
        except:
            Log.error("Failed to disconnect from media server", traceback.format_exc())

    def put(self, source_path: str, target_path: str):
        try:
            self.sftp.put(source_path, target_path)
            Log.debug(f"SFTP PUT {source_path} (HOST) => {target_path} (SERVER)")
            return True
        except Exception:
            Log.error(f"SFTP PUT {source_path} (HOST) => {target_path} (SERVER)", traceback.format_exc())
            return False

    def get(self, source_path: str, target_path: str):
        try:
            self.sftp.get(source_path, target_path)
            Log.debug(f"SFTP GET {source_path} (SERVER) => {target_path} (HOST)")
            return True
        except Exception:
            Log.error(f"SFTP GET {source_path} (SERVER) => {target_path} (HOST)", traceback.format_exc())
            return False
        
    def mkdir(self, path: str):
        try:
            self.sftp.mkdir(path)
            Log.debug(f"SFTP MKDIR {path}")
            return True
        except Exception:
            Log.error(f"SFTP MKDIR {path}", traceback.format_exc())
            return False

    ######### MANGAS #########

    def list_mangas_per_source(self):
        Log.info("Retrieving mangas from media server")

        mangas_in_media_server = []
        sources = self.sftp.listdir(MEDIA_SERVER_PATH_TO_MANGAS)

        Log.debug("Found sources : " + ", ".join(sources))
        
        for source in sources:
            downloaded_mangas = self.sftp.listdir(MEDIA_SERVER_PATH_TO_MANGAS + "/" + source)
            for downloaded_manga in downloaded_mangas:
                mangas_in_media_server.append({"title": downloaded_manga, "source": source})

        Log.debug("Found mangas : " + ", ".join([manga["title"] for manga in mangas_in_media_server]))
        
        return mangas_in_media_server

    def list_manga_chapters(self, manga_title: str, manga_source: str):
        Log.debug(f"Retrieving chapters from {manga_title} [{manga_source}]")
        
        chapters = [file for file in self.sftp.listdir(MEDIA_SERVER_PATH_TO_MANGAS + "/" + manga_source + "/" + manga_title) if file.endswith(".cbz")]
        
        Log.debug(f"Found {len(chapters)} chapters for {manga_title}")
        
        return chapters
    
    def download_manga_chapter(self, manga_title: str, manga_source: str, chapter_name: str, target_dir: str):
        Log.debug(f"Downloading {chapter_name} for {manga_title} [target_dir = {target_dir}]")
        
        source_path = MEDIA_SERVER_PATH_TO_MANGAS + "/" + manga_source + "/" + manga_title + "/" + chapter_name
        target_path = target_dir + "/" + chapter_name
        self.get(source_path, target_path)

    ######### LIGHTNOVELS #########

    def list_lightnovels(self):
        Log.info("Retrieving lightnovels from media server")

        lightnovels_in_media_server = [{"title": directory_name} for directory_name in self.sftp.listdir(MEDIA_SERVER_PATH_TO_LIGHTNOVELS)]

        Log.debug("Found lightnovels : " + ", ".join([lightnovel["title"] for lightnovel in lightnovels_in_media_server]))

        return lightnovels_in_media_server

    def list_lightnovel_chapters(self, lightnovel_title: str):
        Log.debug(f"Retrieving chapters from {lightnovel_title}")
        
        chapters = [file for file in self.sftp.listdir(MEDIA_SERVER_PATH_TO_LIGHTNOVELS + "/" + lightnovel_title) if file.endswith(".epub")]
        
        Log.debug(f"Found {len(chapters)} chapters for {lightnovel_title}")

        return chapters

    def download_lightnovel_chapter(self, lightnovel_title: str, chapter_name: str, target_dir: str):
        Log.debug(f"Downloading {chapter_name} for {lightnovel_title} [target_dir = {target_dir}]")
        
        source_path = MEDIA_SERVER_PATH_TO_LIGHTNOVELS + "/" + lightnovel_title + "/" + chapter_name
        target_path = target_dir + "/" + chapter_name
        self.get(source_path, target_path)

    ######### EBOOKS #########

    def list_ebooks(self):
        Log.info("Retrieving ebooks from media server")

        ebooks = []

        series_found_in_media_server = self.sftp.listdir(MEDIA_SERVER_PATH_TO_EBOOKS)
        Log.debug("Found series : " + ", ".join(series_found_in_media_server))

        for series in series_found_in_media_server:
            ebook_files = [file for file in self.sftp.listdir(MEDIA_SERVER_PATH_TO_EBOOKS + "/" + series) if file.split(".")[-1] in SUPPORTED_EBOOK_FORMATS]
            for ebook_file in ebook_files:
                ebook_title = ".".join(ebook_file.split(".")[0:-1])
                ebook_filetype = ebook_file.split(".")[-1]
                ebooks.append({"title": ebook_title, "series": series, "filetype": ebook_filetype})

            Log.debug("Found ebooks : " + ", ".join([ebook["title"] for ebook in ebooks]))

        return ebooks

    def upload_ebook(self, ebook_path: str, series: str):
        Log.debug(f"Uploading {ebook_path}")

        source_path = ebook_path
        target_path = MEDIA_SERVER_PATH_TO_EBOOKS + "/" + series + "/" + os.path.basename(ebook_path)

        self.mkdir(MEDIA_SERVER_PATH_TO_EBOOKS + "/" + series)
        self.put(source_path, target_path)

    def download_ebook(self, ebook_title: str, ebook_filetype: str, ebook_series: str, target_dir: str):
        Log.debug(f"Downloading {ebook_title} [target_dir = {target_dir}]")

        source_path = MEDIA_SERVER_PATH_TO_EBOOKS + "/" + ebook_series + "/" + f"{ebook_title}.{ebook_filetype}"
        target_path = target_dir + "/" + f"{ebook_title}.{ebook_filetype}"
        self.get(source_path, target_path)