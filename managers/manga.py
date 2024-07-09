from rich.progress import Progress
from typing import List
import traceback
import json
import os

from books.models.manga import Manga
from books.converter import Converter
from connectivity.media_server import MediaServer
from connectivity.ebook_reader import EbookReader
from cli import Cli
from cli.questions import choose_manga, choose_action_for_manga_or_lightnovel, modify_last_chapter_read, get_chapters_download_count
from utils.log import Log

from config import TRACKED_MANGAS_FILE, DOWNLOADS_DIR

class MangaManager:

    tracked_mangas: List[Manga] = []

    def __init__(self):
        if not os.path.isfile(TRACKED_MANGAS_FILE):
            Log.debug(f"Creating {TRACKED_MANGAS_FILE}")
            with open(TRACKED_MANGAS_FILE, "w"): pass

        # First we read tracked mangas from the associated JSON file
        if os.stat(TRACKED_MANGAS_FILE).st_size != 0:
            data = json.load(open(TRACKED_MANGAS_FILE, "r"))
            for entry in data["mangas"]:
                manga = Manga(entry["title"], entry["source"], entry["chapters"], entry["last_read_chapter"])
                self.tracked_mangas.append(manga)
                self.tracked_mangas = sorted(self.tracked_mangas, key=lambda manga: manga.title)

    #### ACTIONS ####

    def update(self):
        media_server = MediaServer()
        media_server.connect()
        
        try:
            Log.info("Updating mangas info")

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

        except Exception:
            Log.error("Failed to sync mangas", traceback.format_exc())

        media_server.disconnect()

    def download_chapters_from_media_server(self, manga: Manga, chapters_count: int):
        if manga.missing:
            input(f"{manga.title} is missing from Media Server ! Press Enter to abort...")
            return None
        
        media_server = MediaServer()
        media_server.connect()
    
        try:
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

        except:
            Log.error(f"Failed to download chapters for {manga.title}", traceback.format_exc())
            target_dir = None

        media_server.disconnect()
        
        print(" ") if target_dir else print("\n[-] Something went wrong when downloading chapters !")
        return target_dir

    def upload_to_reader(self, manga: Manga, source_path: str):
        reader = EbookReader()
        try:
            Log.info(f"Uploading {source_path} to Ebook Reader")

            reader.connect()
            success = reader.upload_book(manga.title, source_path)

        except Exception:
            Log.error(f"Failed to upload {source_path} to Ebook Reader", traceback.format_exc())
            success = False
        
        print(" ") if success else print("\n[-] Something went wrong when uploading to Ebook Reader !")

        reader.disconnect()
        return success

    def save_data(self):
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


    #### MENUS ####

    def book_choice_menu(self):
        stay_in_menu = True

        while stay_in_menu:

            # User chooses a manga in the list of displayed tracked mangas
            chosen_manga = choose_manga(self.tracked_mangas)

            if chosen_manga == "Back":
                stay_in_menu = False

            else:
                manga_title = chosen_manga[0:60].strip()
                manga = next((tracked_manga for tracked_manga in self.tracked_mangas if tracked_manga.title == manga_title), None)
    
                if not manga:
                    Log.warning(f"Could not find {manga_title}")
                    Cli.print(f"Could not find {manga_title}...")
                    input("Go back to main menu")

                else:
                    self.book_action_menu(manga)

    def book_action_menu(self, manga: Manga):
        action = choose_action_for_manga_or_lightnovel()
        
        if action == "Modify last chapter read":
            last_read_chapter = modify_last_chapter_read(manga)
            if last_read_chapter is not None:
                manga.last_read_chapter = last_read_chapter
                Log.debug(f"Modified {manga.title} last read chapter to {last_read_chapter}")

        elif action == "Upload new chapters to Ebook Reader":
            self.chapters_download_menu(manga)

    def chapters_download_menu(self, manga: Manga):
        answer = get_chapters_download_count(manga)
                                        
        if answer != "Back":
            Cli.print("") # Just to get a clean page

            chapters_to_download_count = int(answer)
            downloaded_chapters_folder = self.download_chapters_from_media_server(manga, chapters_to_download_count)

            if downloaded_chapters_folder:
                epub_file = Converter.merge_cbz_to_epub(manga, downloaded_chapters_folder)

                if epub_file:
                    success = self.upload_to_reader(manga, epub_file)

                    if success:
                        manga.last_read_chapter += chapters_to_download_count

            input("Press enter to continue...")

