from typing import List, Union
from rich.progress import Progress
import traceback
import os
import json
import shutil

from cli import Cli
from connectivity.media_server import MediaServer
from connectivity.ebook_reader import EbookReader
from books.models.manga import Manga
from books.models.lightnovel import Lightnovel
from books.models.ebook import Ebook
from utils.log import Log
from config import TRACKED_MANGAS_FILE, TRACKED_LIGHTNOVELS_FILE, TRACKED_EBOOKS_FILE, DOWNLOADS_DIR, APPLICATION_NAME

class BookManager:

    tracked_mangas: List[Manga] = []
    tracked_lightnovels: List[Lightnovel] = []
    tracked_ebooks: List[Ebook] = []

    def __init__(self):
        
        Log.info("Checking whether necessary files and directories exist")

        if not os.path.isfile(TRACKED_MANGAS_FILE):
            Log.debug(f"Creating {TRACKED_MANGAS_FILE}")
            with open(TRACKED_MANGAS_FILE, "w"): pass

        if not os.path.isfile(TRACKED_LIGHTNOVELS_FILE):
            Log.debug(f"Creating {TRACKED_LIGHTNOVELS_FILE}")
            with open(TRACKED_LIGHTNOVELS_FILE, "w"): pass

        if not os.path.isfile(TRACKED_EBOOKS_FILE):
            Log.debug(f"Creating {TRACKED_EBOOKS_FILE}")
            with open(TRACKED_EBOOKS_FILE, "w"): pass

        if not os.path.isdir(DOWNLOADS_DIR):
            Log.debug(f"Creating {DOWNLOADS_DIR}")
            os.mkdir(DOWNLOADS_DIR)

        self.get_tracked_books()

    ############ GENERAL ############

    def get_tracked_books(self):
        Log.info("Retrieving tracked books from JSON files")

        self.get_tracked_mangas()
        self.get_tracked_lightnovels()
        self.get_tracked_ebooks()

    def update_books(self):
        Cli.print("Syncing databases with media server, please wait...")
        Log.info("Syncing books info with media server")

        self.update_mangas_info()
        self.update_lightnovels_info()
        self.update_ebooks_info()

        print("")
        input("Press Enter to continue...")

    def handle_exiting(self, failure=False):
        # Saving data
        self.save_mangas_data()
        self.save_lightnovels_data()
        self.save_ebooks_data()

        # Delete the downloads directory if needed
        for item in os.listdir(DOWNLOADS_DIR):
            item_path = os.path.join(DOWNLOADS_DIR, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        Cli.print(f"Thanks for using {APPLICATION_NAME}, see you soon !") if not failure else Cli.print("Something went wrong, exiting :(")

    def get_book_by_title(self, title: str, category: str):
        for book in getattr(self, "tracked_" + category.lower()):
            if book.title == title:
                return book
            
        return None
    
    def upload_book_to_reader(self, book: Union[Manga, Lightnovel, Ebook], source_path: str):
        reader = EbookReader()
        try:
            Log.info(f"Uploading {source_path} to Ebook Reader")

            reader.connect()
            reader.upload_book(book.title, source_path)
            reader.disconnect()

            return True
        except Exception:
            Log.error(f"Failed to upload {source_path} to Ebook Reader", traceback.format_exc())
            reader.disconnect()
            return False


    ############ MANGAS ############

    def get_tracked_mangas(self):
        if os.stat(TRACKED_MANGAS_FILE).st_size != 0:
            data = json.load(open(TRACKED_MANGAS_FILE, "r"))
            for entry in data["mangas"]:
                manga = Manga(entry["title"], entry["source"], entry["chapters"], entry["last_read_chapter"])
                self.tracked_mangas.append(manga)

    def update_mangas_info(self):
        media_server = MediaServer()
        
        try:
            Log.info("Updating mangas info")

            media_server.connect()

            mangas_in_media_server = media_server.list_mangas_per_source()

            # We compare whether mangas are both tracked and downloaded on the media server or not
            mangas_in_media_server_titles = [manga["title"] for manga in mangas_in_media_server]
            tracked_mangas_titles = [manga.title for manga in self.tracked_mangas]

            for tracked_manga in self.tracked_mangas:
                # First we handle the mangas that are already in our list and are on the media server
                if tracked_manga.title in mangas_in_media_server_titles:
                    chapters = media_server.list_manga_chapters(tracked_manga.title, tracked_manga.source)
                    new_chapters = tracked_manga.update_chapters(chapters)

                    if len(new_chapters) != 0:
                        Log.info(f"New chapters for {tracked_manga.title} : {', '.join(new_chapters)}")
                        print(f"- {tracked_manga.title} => {len(new_chapters)} new chapters")
                
                # Then we handle the mangas that we have in our list but are not on the media server anymore
                else:
                    tracked_manga.missing = True
                    Log.debug(f"{tracked_manga.title} does not exist in media server anymore")

            # Finally we handle the mangas that we don't have in our list
            for downloaded_manga in mangas_in_media_server:
                if downloaded_manga["title"] not in tracked_mangas_titles:
                    new_tracked_manga = Manga(
                        title=downloaded_manga["title"],
                        source=downloaded_manga["source"]
                    )
                    new_tracked_manga.update_chapters(media_server.list_manga_chapters(downloaded_manga["title"], downloaded_manga["source"]))
                    self.tracked_mangas.append(new_tracked_manga)

                    Log.info(f"Added new tracked manga : {new_tracked_manga.title}")
                    print(f"- {new_tracked_manga.title} => **NEW**")

            media_server.disconnect()

        except Exception:
            Log.error("Failed to sync mangas", traceback.format_exc())
            media_server.disconnect()

    def download_manga_chapters(self, manga: Manga, chapters_count: int):
        try:
            media_server = MediaServer()
            media_server.connect()

            target_dir = os.path.join(DOWNLOADS_DIR, manga.title.replace(" ","_"))

            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)

            chapters_to_download = []
            for i in range(chapters_count):
                chapter_id = manga.last_read_chapter + i
                chapter_name = manga.chapters[chapter_id]
                chapters_to_download.append(chapter_name)

            Log.info(f"Downloading following chapters for {manga.title} : {', '.join(chapters_to_download)}")

            with Progress() as progress:
                progress_bar_length = max(1000, len(chapters_to_download))
                task = progress.add_task(f"[red]Downloading {len(chapters_to_download)} chapters for {manga.title}...", total=progress_bar_length)

                for chapter in chapters_to_download:
                    media_server.download_manga_chapter(manga.title, manga.source, chapter, target_dir)
                    progress.update(task, advance=progress_bar_length / len(chapters_to_download))

            media_server.disconnect()

            return target_dir
        except:
            Log.error(f"Failed to download chapters for {manga.title}", traceback.format_exc())
            media_server.disconnect()
            return None

    def save_mangas_data(self):
        Log.info(f"Saving mangas to {TRACKED_MANGAS_FILE}")

        data = {"mangas": []}
        for manga in self.tracked_mangas:
            entry = {
                "title": manga.title,
                "source": manga.source,
                "chapters": manga.chapters,
                "last_read_chapter": manga.last_read_chapter,
                "missing": manga.missing
            }
            data["mangas"].append(entry)
        
        json.dump(data, open(TRACKED_MANGAS_FILE, "w"))

    ############ LIGHTNOVELS ############

    def get_tracked_lightnovels(self):
        if os.stat(TRACKED_LIGHTNOVELS_FILE).st_size != 0:
            data = json.load(open(TRACKED_LIGHTNOVELS_FILE, "r"))
            for entry in data["lightnovels"]:
                lightnovel = Lightnovel(entry["title"], entry["chapters"], entry["last_read_chapter"])
                self.tracked_lightnovels.append(lightnovel)

    def update_lightnovels_info(self):
        try:
            Log.info("Updating lightnovels info")
        except Exception:
            Log.error("Failed to sync lightnovels", traceback.format_exc())

    def save_lightnovels_data(self):
        Log.info(f"Saving lightnovels to {TRACKED_LIGHTNOVELS_FILE}")

        data = {"lightnovels": []}
        for lightnovel in self.tracked_lightnovels:
            entry = {
                "title": lightnovel.title,
                "chapters": lightnovel.chapters,
                "last_read_chapter": lightnovel.last_read_chapter,
                "missing": lightnovel.missing
            }
            data["lightnovels"].append(entry)

        json.dump(data, open(TRACKED_LIGHTNOVELS_FILE, "w"))

    ############ EBOOKS ############

    def get_tracked_ebooks(self):
        if os.stat(TRACKED_EBOOKS_FILE).st_size != 0:
            data = json.load(open(TRACKED_EBOOKS_FILE, "r"))
            for entry in data["ebooks"]:
                ebook = Ebook(entry["title"], entry["read"])
                self.tracked_ebooks.append(ebook)

    def update_ebooks_info(self):
        try:
            Log.info("Updating ebooks info")
        except Exception:
            Log.error("Failed to sync ebooks", traceback.format_exc())
    
    def save_ebooks_data(self):
        Log.info(f"Saving ebooks to {TRACKED_EBOOKS_FILE}")

        data = {"ebooks": []}
        for ebook in self.tracked_ebooks:
            entry = {
                "title": ebook.title,
                "read": ebook.read,
                "missing": ebook.missing
            }
            data["ebooks"].append(entry)

        json.dump(data, open(TRACKED_EBOOKS_FILE, "w"))