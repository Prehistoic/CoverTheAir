from rich.progress import Progress
from typing import List
import traceback
import json
import os

from books.models.lightnovel import Lightnovel
from books.converter import Converter
from connectivity.media_server import MediaServer
from connectivity.ebook_reader import EbookReader
from cli import Cli
from cli.questions import choose_lightnovel, choose_action_for_manga_or_lightnovel, modify_last_chapter_read, get_chapters_download_count
from utils.log import Log

from config import TRACKED_LIGHTNOVELS_FILE, DOWNLOADS_DIR

class LightnovelManager:

    tracked_lightnovels: List[Lightnovel] = []

    def __init__(self):
        if not os.path.isfile(TRACKED_LIGHTNOVELS_FILE):
            Log.debug(f"Creating {TRACKED_LIGHTNOVELS_FILE}")
            with open(TRACKED_LIGHTNOVELS_FILE, "w"): pass

        # First we read tracked lightnovels from the associated JSON file
        if os.stat(TRACKED_LIGHTNOVELS_FILE).st_size != 0:
            data = json.load(open(TRACKED_LIGHTNOVELS_FILE, "r"))
            for entry in data["lightnovels"]:
                lightnovel = Lightnovel(entry["title"], entry["source"], entry["chapters"], entry["last_read_chapter"])
                self.tracked_lightnovels.append(lightnovel)

    #### ACTIONS ####

    def update(self):
        media_server = MediaServer()
        media_server.connect()

        try:
            Log.info("Updating lightnovels info")

            lightnovels_in_media_server = media_server.list_lightnovels()

            # We compare whether lightnovels are both tracked and downloaded on the media server or not
            lightnovels_in_media_server_titles = [lightnovel["title"] for lightnovel in lightnovels_in_media_server]
            tracked_lightnovels_titles = [lightnovel.title for lightnovel in self.tracked_lightnovels]

            for tracked_lightnovel in self.tracked_lightnovels:
                # First we handle the lightnovels that are already in our list and are on the media server
                if tracked_lightnovel.title in lightnovels_in_media_server_titles:
                    chapters = media_server.list_lightnovel_chapters(tracked_lightnovel.title)
                    new_chapters = tracked_lightnovel.update_chapters(chapters)

                    if len(new_chapters) != 0:
                        Log.info(f"New chapters for {tracked_lightnovel.title} : {', '.join(new_chapters)}")
                        print(f"- {tracked_lightnovel.title} => {len(new_chapters)} new chapters")
                
                # Then we handle the lightnovels that we have in our list but are not on the media server anymore
                else:
                    tracked_lightnovel.missing = True
                    Log.debug(f"{tracked_lightnovel.title} does not exist in media server anymore")

            # Finally we handle the mangas that we don't have in our list
            for downloaded_lightnovel in lightnovels_in_media_server:
                if downloaded_lightnovel["title"] not in tracked_lightnovels_titles:
                    new_tracked_lightnovel = Lightnovel(
                        title=downloaded_lightnovel["title"]
                    )
                    new_tracked_lightnovel.update_chapters(media_server.list_lightnovel_chapters(downloaded_lightnovel["title"]))
                    self.tracked_lightnovels.append(new_tracked_lightnovel)

                    Log.info(f"Added new tracked lightnovel : {new_tracked_lightnovel.title}")
                    print(f"- {new_tracked_lightnovel.title} => **NEW**")
        except Exception:
            Log.error("Failed to sync lightnovels", traceback.format_exc())

        media_server.disconnect()

    def download_chapters_from_media_server(self, lightnovel: Lightnovel, chapters_count: int):
        if lightnovel.missing:
            input(f"{lightnovel.title} is missing from Media Server ! Press Enter to abort...")
            return None
        
        media_server = MediaServer()
        media_server.connect()

        try:
            target_dir = os.path.join(DOWNLOADS_DIR, lightnovel.title.replace(" ","_"))

            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)

            chapters_to_download = []
            for i in range(chapters_count):
                chapter_id = lightnovel.last_read_chapter + i
                chapter_name = lightnovel.chapters[chapter_id]
                chapters_to_download.append(chapter_name)

            Log.info(f"Downloading following chapters for {lightnovel.title} : {', '.join(chapters_to_download)}")

            with Progress() as progress:
                progress_bar_length = max(1000, len(chapters_to_download))
                task = progress.add_task(f"[red]Downloading {len(chapters_to_download)} chapters for {lightnovel.title}...", total=progress_bar_length)

                for chapter in chapters_to_download:
                    media_server.download_lightnovel_chapter(lightnovel.title, chapter, target_dir)
                    progress.update(task, advance=progress_bar_length / len(chapters_to_download))

        except:
            Log.error(f"Failed to download chapters for {lightnovel.title}", traceback.format_exc())
            target_dir = None

        media_server.disconnect()
        
        print(" ") if target_dir else print("\n[-] Something went wrong when downloading chapters !")
        return target_dir
    
    def upload_to_reader(self, lightnovel: Lightnovel, source_path: str):
        reader = EbookReader()
        try:
            Log.info(f"Uploading {source_path} to Ebook Reader")

            reader.connect()
            success = reader.upload_book(lightnovel.title, source_path)

        except Exception:
            Log.error(f"Failed to upload {source_path} to Ebook Reader", traceback.format_exc())
            success = False
        
        print(" ") if success else print("\n[-] Something went wrong when uploading to Ebook Reader !")

        reader.disconnect()
        return success
    
    def save_data(self):
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

    
    #### MENUS ####

    def book_choice_menu(self):
        stay_in_menu = True

        while stay_in_menu:

            # User chooses a lightnovel in the list of displayed tracked lightnovels
            chosen_lightnovel = choose_lightnovel(self.tracked_lightnovels)

            if chosen_lightnovel == "Back":
                stay_in_menu = False

            else:
                lightnovel_title = chosen_lightnovel[0:60].strip()
                lightnovel = next((tracked_lightnovel for tracked_lightnovel in self.tracked_lightnovels if tracked_lightnovel.title == lightnovel_title), None)
    
                if not lightnovel:
                    Log.warning(f"Could not find {lightnovel_title}")
                    Cli.print(f"Could not find {lightnovel_title}...")
                    input("Go back to main menu")

                else:
                    self.book_action_menu(lightnovel)

    def book_action_menu(self, lightnovel: Lightnovel):
        action = choose_action_for_manga_or_lightnovel()
        
        if action == "Modify last chapter read":
            last_read_chapter = modify_last_chapter_read(lightnovel)
            if last_read_chapter:
                lightnovel.last_read_chapter = last_read_chapter
                Log.debug(f"Modified {lightnovel.title} last read chapter to {last_read_chapter}")

        elif action == "Upload new chapters to Ebook Reader":
            self.chapters_download_menu(lightnovel)

    def chapters_download_menu(self, lightnovel: Lightnovel):
        answer = get_chapters_download_count(lightnovel)
                                        
        if answer != "Back":
            Cli.print("") # Just to get a clean page

            chapters_to_download_count = int(answer)
            downloaded_chapters_folder = self.download_chapters_from_media_server(lightnovel, chapters_to_download_count)

            if downloaded_chapters_folder:
                epub_file = Converter.merge_epubs_to_epub(lightnovel, downloaded_chapters_folder)

                if epub_file:
                    success = self.upload_to_reader(lightnovel, epub_file)

                    if success:
                        lightnovel.last_read_chapter += chapters_to_download_count

            input("Press enter to continue...")