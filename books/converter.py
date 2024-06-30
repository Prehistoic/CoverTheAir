import os
import traceback
from rich.progress import Progress
from ebooklib import epub, ITEM_DOCUMENT, ITEM_COVER

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
            
        print(" ") if not epub_file else print("\n[-] Something went wrong when merging files to .epub !")
        return epub_file
    
    @classmethod
    def merge_epubs_to_epub(self, lightnovel: Lightnovel, directory: str):
        try:
            merged_epub = epub.EpubBook()
            merged_epub.set_title(lightnovel.title)

            style = '''
    
            h2 {
                text-align: center;
                font-size: 100px;
                font-family: Tahoma, Geneva, sans-serif;
            }

            p { 
                font-size: 50px; 
                font-family: Tahoma, Geneva, sans-serif;
            }
            
            '''
            default_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            merged_epub.add_item(default_css)

            # Initialize the merged content list
            chapters = []
            toc = []

            # Loop through all files in the directory
            merged_epub_got_cover = False
            merged_epub_got_author = False
            chapter_id = 0
            
            with Progress() as progress:

                epub_files = [file for file in os.listdir(directory) if file.endswith(".epub")]

                progress_bar_length = len(epub_files) * 100 + 100
                task = progress.add_task(f"[red]Merging EPUBs from {directory}...", total=progress_bar_length)

                for idx, filename in enumerate(epub_files):
                    epub_path = os.path.join(directory, filename)
                    book = epub.read_epub(name=epub_path, options={"ignore_ncx": True})

                    # Retrieving the author from the first .epub
                    if not merged_epub_got_author:
                        try:
                            creator_metadata = book.get_metadata(namespace="DC", name="creator")
                            author = creator_metadata[0][0]
                            merged_epub.add_author(author)
                            merged_epub_got_author = True
                        except:
                            pass

                    for item in book.get_items():
                        # Retrieving every chapter
                        if item.get_type() == ITEM_DOCUMENT and item.get_name().startswith("Chapter "):
                            chapter_id += 1

                            chapter = epub.EpubHtml(
                                uid=f"chapter_{chapter_id}",
                                file_name=item.get_name(),
                                content=item.get_content()
                            )

                            # Making sure the text is formatted correctly
                            chapter.add_item(default_css)
                            
                            merged_epub.add_item(chapter)
                            chapters.append(chapter)
                            toc.append(epub.Link(chapter.get_name(), chapter.get_name().split(".")[0], chapter.get_id()))

                        # Retrieving the cover from the first .epub
                        elif item.get_type() == ITEM_COVER and not merged_epub_got_cover:
                            merged_epub.set_cover(item.get_name(), item.get_content())
                            merged_epub_got_cover = True
                    
                    # Updating progress
                    progress.advance(task, advance=idx * 100)

                # Create the spine, ncx, nav and TOC
                merged_epub.toc = tuple(toc)
                merged_epub.add_item(epub.EpubNcx())
                merged_epub.add_item(epub.EpubNav())
                merged_epub.spine = chapters            

                # Write the merged EPUB to the output file
                epub_file = os.path.join(directory, lightnovel.title + ".epub")
                epub.write_epub(name=epub_file, book=merged_epub)

                progress.advance(task, advance=100)
        
        except Exception:
            Log.error(f"Failed to merge .epub files from {directory} to .epub", traceback.format_exc())
            epub_file = None

        print(" ") if epub_file else print("\n[-] Something went wrong when merging files to .epub !")
        return epub_file

