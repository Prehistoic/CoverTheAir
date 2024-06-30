import os
import traceback
from ebooklib import epub, ITEM_DOCUMENT

from books.models.manga import Manga
from books.models.lightnovel import Lightnovel
from books.formats.cbz import Cbz
from books.formats.epub import EPubMaker
from utils.comicinfo import ComicInfo
from utils.log import Log

class Converter:

    @classmethod
    def merge_cbz_to_epub(self, manga: Manga, directory: str):
        try:
            author = ""

            for idx, cbz_filename in enumerate([filename for filename in  os.listdir(directory) if filename.endswith(".cbz")]):
                cbz = Cbz(os.path.join(directory, cbz_filename))
                output_directory = cbz.unzip()
                
                # We try to find the writer by parsing ComicInfo.xml from the 1st downloaded chapter
                if idx == 0:
                    for filename in os.listdir(output_directory):
                        if filename.lower() == "comicinfo.xml":
                            comic_info = ComicInfo(os.path.join(output_directory, filename))
                            author = comic_info.get_writer()
            
            epub_file = os.path.join(directory, manga.title.replace(" ","_") + ".epub")
            
            EPubMaker(
                master=None,
                input_dir=directory,
                file=epub_file,
                name=manga.title,
                author=author,
                wrap_pages=True,
                grayscale=False,
                max_width=None,
                max_height=None
            ).run()
        
        except Exception:
            Log.error(f"Failed to merge .cbz files from {directory} to .epub", traceback.format_exc())
            epub_file = None
            
        print(" ") if epub_file else print("\n[-] Something went wrong when merging files to .epub !")
        return epub_file
    
    @classmethod
    def merge_epubs_to_epub(self, lightnovel: Lightnovel, directory: str):
        try:
            merged_epub = epub.EpubBook()
            merged_epub.set_title(lightnovel.title)

            # Initialize the merged content list
            merged_content = []

            # Loop through all files in the directory
            for filename in os.listdir(directory):
                if filename.endswith(".epub"):
                    epub_path = os.path.join(directory, filename)
                    book = epub.read_epub(epub_path)

                    # Add all items (content) from the current book to the merged book
                    for item in book.get_items():
                        if item.get_type() == ITEM_DOCUMENT:
                            merged_content.append(item)
                            merged_epub.add_item(item)

                if filename.split(".")[-1] in ["jpg", "jpeg", "png"]:
                    image_path = os.path.join(directory, filename)
                    with open(image_path, "rb") as img_file:
                        cover_data = img_file.read()
                        
                    merged_epub.set_cover("cover.jpg", cover_data)

            # Create the spine and TOC
            merged_epub.toc = (epub.Link(item.file_name, item.get_name(), item.get_id()) for item in merged_content)
            merged_epub.spine = ['nav'] + merged_content

            # Add default NCX and Nav file
            merged_epub.add_item(epub.EpubNcx())
            merged_epub.add_item(epub.EpubNav())

            # Write the merged EPUB to the output file
            epub_file = os.path.join(directory, lightnovel.title.replace(" ","_") + ".epub")
            epub.write_epub(epub_file, merged_epub, {})
        
        except Exception:
            Log.error(f"Failed to merge .epub files from {directory} to .epub", traceback.format_exc())
            epub_file = None

        print(" ") if epub_file else print("\n[-] Something went wrong when merging files to .epub !")
        return epub_file

