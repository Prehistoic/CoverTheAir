import os

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
            Log.warning(f"Failed to merge .cbz files from {directory} to .epub")
            epub_file = None
            
        print(" ") if epub_file else print("\n[-] Something went wrong when merging files to .epub !")
        return epub_file
    
    @classmethod
    def merge_epub_to_epub(self, lightnovel: Lightnovel, directory: str):
        return None
