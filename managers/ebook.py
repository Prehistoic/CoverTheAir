from rich.progress import Progress
from typing import List
import traceback
import json
import os

from books.models.ebook import Ebook
from connectivity.media_server import MediaServer
from connectivity.ebook_reader import EbookReader
from cli import Cli
from cli.questions import choose_ebook, choose_action_for_ebook, choose_local_ebook_to_upload, modify_read_status, choose_series
from utils.log import Log

from config import TRACKED_EBOOKS_FILE, DOWNLOADS_DIR

class EbookManager:

    tracked_ebooks: List[Ebook] = []

    def __init__(self):
        if not os.path.isfile(TRACKED_EBOOKS_FILE):
            Log.debug(f"Creating {TRACKED_EBOOKS_FILE}")
            with open(TRACKED_EBOOKS_FILE, "w"): pass

        # First we read tracked ebooks from the associated JSON file
        if os.stat(TRACKED_EBOOKS_FILE).st_size != 0:
            data = json.load(open(TRACKED_EBOOKS_FILE, "r"))
            for entry in data["ebooks"]:
                ebook = Ebook(entry["title"], entry["series"], entry["read"], entry["filetype"])
                self.tracked_ebooks.append(ebook)
                self.tracked_ebooks = sorted(self.tracked_ebooks, key=lambda ebook: ebook.title)

    def update(self):
        media_server = MediaServer()
        media_server.connect()
        
        try:
            Log.info("Updating ebooks info")
            ebooks_in_media_server = media_server.list_ebooks()

             # We compare whether ebooks are both tracked and downloaded on the media server or not
            ebooks_in_media_server_titles = [ebook["title"] for ebook in ebooks_in_media_server]
            tracked_ebooks_titles = [ebook.title for ebook in self.tracked_ebooks]

            for tracked_ebook in self.tracked_ebooks:
                # First we handle the ebooks that are already in our list but are not on the media server anymore
                if tracked_ebook.title not in ebooks_in_media_server_titles:
                    tracked_ebook.missing = True
                    Log.debug(f"{tracked_ebook.title} does not exist in media server anymore")

            # Finally we handle the ebooks that we don't have in our list
            for downloaded_ebook in ebooks_in_media_server:
                if downloaded_ebook["title"] not in tracked_ebooks_titles:
                    new_tracked_ebook = Ebook(
                        title=downloaded_ebook["title"],
                        series=downloaded_ebook["series"],
                        filetype=downloaded_ebook["filetype"]
                    )
                    self.tracked_ebooks.append(new_tracked_ebook)

                    Log.info(f"Added new tracked ebook : {new_tracked_ebook.title}")
                    print(f"- {new_tracked_ebook.title} => **NEW**")
        except Exception:
            Log.error("Failed to sync ebooks", traceback.format_exc())

        media_server.disconnect()

    def download_from_media_server(self, ebook: Ebook):
        if ebook.missing:
            input(f"{ebook.title} is missing from Media Server ! Press Enter to abort...")
            return None

        media_server = MediaServer()
        media_server.connect()
    
        try:
            with Progress() as progress:
                progress_bar_length = 1000
                task = progress.add_task(f"[red]Downloading {ebook.title}...", total=progress_bar_length)

                media_server.download_ebook(ebook.title, ebook.filetype, ebook.series, DOWNLOADS_DIR)
                progress.update(task, advance=progress_bar_length)

            media_server.disconnect()

            downloaded_ebook = os.path.join(DOWNLOADS_DIR, f"{ebook.title}.{ebook.filetype}")
        except:
            Log.error(f"Failed to download {ebook.title}", traceback.format_exc())
            downloaded_ebook = None

        media_server.disconnect()
        
        print(" ") if downloaded_ebook else print("\n[-] Something went wrong when downloading ebook !")
        return downloaded_ebook

    def upload_to_media_server(self, ebook_path: str, ebook_series: str):
        media_server = MediaServer()
        media_server.connect()

        try:
            Log.info(f"Uploading {ebook_path} to Media Server...")
            Cli.print(f"Uploading {ebook_path} to Media Server... ", end="")

            media_server.upload_ebook(ebook_path, ebook_series)

            print("done")
        except Exception:
            Log.error(f"Failed to upload {ebook_path} to Media Server", traceback.format_exc())
            print("error")
        
        media_server.disconnect()

    def upload_to_reader(self, ebook: Ebook, source_path: str):
        reader = EbookReader()
        try:
            Log.info(f"Uploading {source_path} to Ebook Reader")

            reader.connect()
            success = reader.upload_book(ebook.title, source_path)

        except Exception:
            Log.error(f"Failed to upload {source_path} to Ebook Reader", traceback.format_exc())
            success = False
        
        print(" ") if success else print("\n[-] Something went wrong when uploading to Ebook Reader !")

        reader.disconnect()
        return success

    def save_data(self):
        Log.info(f"Saving ebooks to {TRACKED_EBOOKS_FILE}")

        data = {"ebooks": []}
        for ebook in self.tracked_ebooks:
            entry = {
                "title": ebook.title,
                "series": ebook.series,
                "read": ebook.read,
                "filetype": ebook.filetype,
                "missing": ebook.missing
            }
            data["ebooks"].append(entry)

        json.dump(data, open(TRACKED_EBOOKS_FILE, "w"))


    #### MENUS ####

    def book_choice_menu(self):
        stay_in_menu = True

        while stay_in_menu:

            # User chooses an ebook in the list of displayed tracked ebooks
            chosen_ebook = choose_ebook(self.tracked_ebooks)

            if chosen_ebook == "Back":
                stay_in_menu = False

            elif chosen_ebook == "Upload local ebook to Media Server":
                local_path = choose_local_ebook_to_upload()
                if local_path:
                    series = choose_series()
                    self.upload_to_media_server(local_path, series)
                    self.update()

            else:
                ebook_title = chosen_ebook[0:60].strip()
                ebook = next((tracked_ebook for tracked_ebook in self.tracked_ebooks if tracked_ebook.title == ebook_title), None)
    
                if not ebook:
                    Log.warning(f"Could not find {ebook_title}")
                    Cli.print(f"Could not find {ebook_title}...")
                    input("Go back to main menu")

                else:
                    self.book_action_menu(ebook)

    def book_action_menu(self, ebook: Ebook):
        action = choose_action_for_ebook()
        
        if action == "Modify read status":
            ebook.read = modify_read_status(ebook)
            Log.debug(f"Modified {ebook.title} read status to {ebook.read}")

        elif action == "Upload to Ebook Reader":
            self.download_menu(ebook)

    def download_menu(self, ebook: Ebook):
        Cli.print("") # Just to get a clean page

        downloaded_file = self.download_from_media_server(ebook)

        if downloaded_file:
            success = self.upload_to_reader(ebook, downloaded_file)

            if success:
                ebook.read = True

        input("Press enter to continue...")

