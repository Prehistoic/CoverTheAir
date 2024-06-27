import os
import sys
import traceback
import shutil

from cli import Cli
from cli.questions import main_menu
from managers.manga import MangaManager
from managers.lightnovel import LightnovelManager
from managers.ebook import EbookManager
from utils.log import Log
from config import APPLICATION_NAME, DOWNLOADS_DIR

class CoverTheAir:

    def __init__(self):
        self.manga_manager = MangaManager()
        self.lightnovel_manager = LightnovelManager()
        self.ebook_manager = EbookManager()

        # We need to make sure we got our downloads/ directory
        if not os.path.isdir(DOWNLOADS_DIR):
            Log.debug(f"Creating {DOWNLOADS_DIR}")
            os.mkdir(DOWNLOADS_DIR)

    def update_books(self):
        # First we need to make sure everything source of books from the Media Server is up to date
        Cli.print("Syncing databases with media server, please wait...")
        Log.info("Syncing books info with media server")
        
        self.manga_manager.update()
        self.lightnovel_manager.update()
        self.ebook_manager.update()
        
        print("")
        input("Press Enter to continue...")

    def go_to_book_choice_menu(self, book_type: str):
        if book_type.lower() == "mangas":
            self.manga_manager.book_choice_menu()
        elif book_type.lower() == "lightnovels":
            self.lightnovel_manager.book_choice_menu()
        else:
            self.ebook_manager.book_choice_menu()

    def handle_exiting(self, failure=False):
        # Saving data
        self.manga_manager.save_data()
        self.lightnovel_manager.save_data()
        self.ebook_manager.save_data()

        # Delete the downloads directory if needed
        for item in os.listdir(DOWNLOADS_DIR):
            item_path = os.path.join(DOWNLOADS_DIR, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        Cli.print(f"Thanks for using {APPLICATION_NAME}, see you soon !") if not failure else Cli.print("Something went wrong, exiting :(")


def main():
    covertheair = CoverTheAir()

    try:
        # First we update our database based on what is on the server
        covertheair.update_books()

        keep_going = True
        while keep_going:

            # We display the main menu where the user can choose which types of media he wants to look at
            chosen_option = main_menu()

            if chosen_option == "Quit CoverTheAir":
                keep_going = False
            else:
                covertheair.go_to_book_choice_menu(chosen_option)

    except KeyboardInterrupt:
        covertheair.handle_exiting()
        sys.exit(-1)
    except Exception:
        Log.error("Something wrong happened !", traceback.format_exc())
        covertheair.handle_exiting(failure=True)
        sys.exit(-1)

    covertheair.handle_exiting()
    sys.exit(0)


if __name__=="__main__":
    main()