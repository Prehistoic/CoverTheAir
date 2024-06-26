import sys
import traceback

from cli.questions import *
from cli.prettyfy import pprint, pprompt
from books.manager import BookManager
from books.converter import merge_cbz_to_epub
from utils.log import Log

def covertheair():
    manager = BookManager()

    try:
        # First we update our database based on what is on the server
        manager.update_books()
        
        keep_going = True

        while keep_going:

            # We display the main menu where the user can choose which types of media he wants to look at
            chosen_option = pprompt(main_menu_question)["main_menu"]
            if chosen_option == "Quit CoverTheAir":
                keep_going = False

            else:
                stay_on_books_menu = True
                
                while stay_on_books_menu:

                    # We display the list of the books of the chosen category that are currently tracked
                    books_menu = generate_books_menu(getattr(manager, "tracked_" + chosen_option.lower()), chosen_option.lower())
                    chosen_book = pprompt(books_menu)["books_menu"]

                    if chosen_book == "Back":
                        stay_on_books_menu = False

                    else:
                        book_title = chosen_book[0:60].strip()
                        book_category = chosen_option.lower()

                        book = manager.get_book_by_title(book_title, book_category)

                        if not book:
                            Log.warning(f"Could not find book {book_title} in {book_category}")
                            pprint(f"Could not find book {book_title} in {book_category}...")
                            input("Go back to main menu")

                        else:
                            if book_category in ["mangas", "lightnovels"]:
                                action = pprompt(chosen_manga_or_lightnovel_question)["chosen_book"]

                                if action == "Modify last chapter read":
                                    last_read_chapter = int(pprompt(generate_modify_last_chapter_read_question(book))["modify_last_chapter_read"])
                                    book.last_read_chapter = last_read_chapter
                                    Log.debug(f"Modified {book.title} last read chapter to {last_read_chapter}")

                                elif action == "Upload new chapters to Ebook Reader":
                                    chapters_download_count_question = generate_chapters_download_count_question(book)
                                    
                                    # We don't try to download if there's nothing new to download
                                    if chapters_download_count_question:
                                        answer = pprompt(chapters_download_count_question)["chapters_download_count"]
                                        
                                        if answer != "Back":
                                            pprint("") # Just to get a clean page
                                            
                                            chapters_to_download_count = int(answer)
                                            
                                            if book_category == "mangas":
                                                downloaded_chapters_folder = manager.download_manga_chapters(book, chapters_to_download_count)

                                                print(" ")
                                                
                                                if downloaded_chapters_folder:
                                                    epub_file = merge_cbz_to_epub(book, downloaded_chapters_folder)
                                                    
                                                    if epub_file:
                                                        print(" ")

                                                        success = manager.upload_book_to_reader(book, epub_file)

                                                        if success:
                                                            book.last_read_chapter += chapters_to_download_count

                                                        else:
                                                            print("\n[-] Something went wrong when uploading to Ebook Reader !")

                                                    else:
                                                        print("\n[-] Something went wrong when merging files to .epub !")

                                                else:
                                                    print("\n[-] Something went wrong when downloading chapters !")

                                            print(" ")
                                            input("Press enter to continue...")

                                    else:
                                        pprint("There is no new chapter to download !")
                                        input("Press enter to continue...")

                            else:
                                action = pprompt(chosen_ebook_question)["chosen_book"]

                                if action == "Modify read status":
                                    read_status = pprompt(read_status_question)["read_status"] == "Yes"
                                    book.read = read_status
                                    Log.debug(f"Modified {book.title} read status to {read_status}")

                                elif action == "Upload to Ebook Reader":
                                    pass
    
    except KeyboardInterrupt:
        manager.handle_exiting()
        sys.exit(-1)
    except Exception:
        Log.error("Something wrong happened !", traceback.format_exc())
        manager.handle_exiting(failure=True)
        sys.exit(-1)

    manager.handle_exiting()
    sys.exit(0)


if __name__=="__main__":
    covertheair()