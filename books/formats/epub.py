import os
import re
import threading
import traceback
import uuid
from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from rich.progress import Progress

import PIL.Image
from ebooklib import epub
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from utils.log import Log

MEDIA_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif', '.jpeg': 'image/jpeg'}
TEMPLATE_DIR = Path(__file__).parent.joinpath("epub_templates")

def natural_keys(text):
    """
    http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]


def filter_images(files):
    files.sort(key=natural_keys)
    for x in files:
        _, extension = os.path.splitext(x)
        file_type = MEDIA_TYPES.get(extension)
        if file_type:
            yield x, file_type, extension


class Chapter:
    def __init__(self, dir_path, title, start: str = None):
        self.dir_path = dir_path
        self.title = title
        self.children: List[Chapter] = []
        self._start = start

    @property
    def start(self) -> Optional[str]:
        if self._start:
            return self._start
        if self.children:
            return self.children[0].start

    @start.setter
    def start(self, value):
        self._start = value

    @property
    def depth(self) -> int:
        if self.children:
            return 1 + max(child.depth for child in self.children)
        return 1


class EPubMaker(threading.Thread):
    def __init__(self, master, input_dir, file, name, author, wrap_pages, grayscale, max_width, max_height):
        threading.Thread.__init__(self)
        self.master = master
        self.dir = input_dir
        self.file = file
        self.name = name
        self.picture_at = 1
        self.stop_event = False

        self.template_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), undefined=StrictUndefined)

        self.zip: Optional[ZipFile] = None
        self.cover = None
        self.author = author
        self.chapter_tree: Optional[Chapter] = None
        self.images = []
        self.uuid = 'urn:uuid:' + str(uuid.uuid1())
        self.grayscale = grayscale
        self.max_width = max_width
        self.max_height = max_height
        self.wrap_pages = wrap_pages

    def run(self):
        try:
            assert os.path.isdir(self.dir), Log.warning("The given directory does not exist!")
            assert self.name, Log.warning("No name given!")

            self.make_epub()

            if self.master is None:
                Log.info(f"EPUB {self.file} created !")
            else:
                self.master.generic_queue.put(lambda: self.master.stop(1))

        except Exception as e:
            if not isinstance(e, StopException):
                if self.master is not None:
                    self.master.generic_queue.put(lambda: self.master.showerror(
                        "Error encountered",
                        "The following error was thrown:\n{}".format(e)
                    ))
                else:
                    Log.error(f"Failed to build EPUB {self.file}", traceback.print_exc())
            try:
                if os.path.isfile(self.file):
                    os.remove(self.file)
            except IOError:
                pass

    def make_epub(self):
        with ZipFile(self.file, mode='w', compression=ZIP_DEFLATED) as self.zip:
            self.zip.writestr('mimetype', 'application/epub+zip', compress_type=ZIP_STORED)
            self.add_file('META-INF', "container.xml")
            self.add_file('stylesheet.css')
            self.make_tree()
            self.assign_image_ids()
            self.write_images()
            self.write_template('package.opf')
            self.write_template('toc.xhtml')
            self.write_template('toc.ncx')

    def add_file(self, *path: str):
        self.zip.write(TEMPLATE_DIR.joinpath(*path), os.path.join(*path))

    def make_tree(self):
        root = Path(self.dir)
        self.chapter_tree = Chapter(root.parent, None)
        chapter_shortcuts = {root.parent: self.chapter_tree}

        for dir_path, dir_names, filenames in os.walk(self.dir):
            dir_names.sort(key=natural_keys)
            images = self.get_images(filenames, dir_path)
            dir_path = Path(dir_path)
            chapter = Chapter(dir_path, dir_path.name, images[0] if images else None)
            chapter_shortcuts[dir_path.parent].children.append(chapter)
            chapter_shortcuts[dir_path] = chapter

        while len(self.chapter_tree.children) == 1:
            self.chapter_tree = self.chapter_tree.children[0]

    def get_images(self, files, root):
        result = []
        for x, file_type, extension in filter_images(files):
            data = self.add_image(os.path.join(root, x), file_type, extension)
            result.append(data)
            if not self.cover and 'cover' in x.lower():
                self.cover = data
                data["is_cover"] = True
        return result

    def add_image(self, source, file_type, extension):
        data = {"extension": extension, "type": file_type, "source": source, "is_cover": False}
        self.images.append(data)
        return data

    def assign_image_ids(self):
        if not self.cover and self.images:
            cover = self.images[0]
            cover["is_cover"] = True
            self.cover = cover
        padding_width = len(str(len(self.images)))
        for count, image in enumerate(self.images):
            image["id"] = f"image_{count:0{padding_width}}"
            image["filename"] = image["id"] + image["extension"]

    def write_images(self):
        template = self.template_env.get_template("page.xhtml.jinja2")

        with Progress() as progress:

            progress_bar_length = len(self.images) * 100
            task = progress.add_task(f"[red]Creating {os.path.basename(self.file)}...", total=progress_bar_length)

            for idx, image in enumerate(self.images):
                output = os.path.join('images', image["filename"])
                image_data: PIL.Image.Image = PIL.Image.open(image["source"])
                image["width"], image["height"] = image_data.size
                image["type"] = image_data.get_format_mimetype()
                should_resize = (self.max_width and self.max_width < image["width"]) or (
                            self.max_height and self.max_height < image["height"])
                should_grayscale = self.grayscale and image_data.mode != "L"
                if not should_grayscale and not should_resize:
                    self.zip.write(image["source"], output)
                else:
                    image_format = image_data.format
                    if should_resize:
                        width_scale = image["width"] / self.max_width if self.max_width else 1.0
                        height_scale = image["height"] / self.max_height if self.max_height else 1.0
                        scale = max(width_scale, height_scale)
                        image_data = image_data.resize((int(image["width"] / scale), int(image["height"] / scale)))
                        image["width"], image["height"] = image_data.size
                    if should_grayscale:
                        image_data = image_data.convert("L")
                    with self.zip.open(output, "w") as image_file:
                        image_data.save(image_file, format=image_format)

                if self.wrap_pages:
                    self.zip.writestr(os.path.join("pages", image["id"] + ".xhtml"), template.render(image))

                progress.advance(task, advance=idx * 100)
                self.check_is_stopped()

    def write_template(self, name, *, out=None, data=None):
        out = out or name
        data = data or {
            "name": self.name, "uuid": self.uuid, "cover": self.cover, "chapter_tree": self.chapter_tree,
            "images": self.images, "wrap_pages": self.wrap_pages, "author": self.author
        }
        self.zip.writestr(out, self.template_env.get_template(name + '.jinja2').render(data))

    def stop(self):
        self.stop_event = True

    def check_is_stopped(self):
        if self.stop_event:
            raise StopException()


class StopException(Exception):
    def __str__(self):
        return "EPUB creator has been stopped!"
    
########################################################################################
########################################################################################
########################################################################################

def create_epub_from_xhtml(book_title: str, book_author: str, folder_path: str):
    out_epub = os.path.join(folder_path, book_title + ".epub")

    book = epub.EpubBook()
    book.set_title(book_title)
    book.add_author(book_author)

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
    book.add_item(default_css)

    chapters = []
    chapter_files = []
    toc = []
    files = os.listdir(folder_path)
    for file in files:
        filename = file.split('.')[0]
        ext = file.split('.')[-1].lower()
        if ext in ["png", "jpg"]:
            book.set_cover('image.jpg', open(folder_path + "/" + file, 'rb').read())
        elif ext == "xhtml" and filename.isdigit():
            chapter_files.append(file)

    # We re-order chapter_files
    chapter_files.sort(key=lambda e: int(e.split('.')[0]))

    for file in chapter_files:
        filename = file.split('.')[0]
        chapter_number = int(filename)
        chapter_content = open(folder_path + "/" + file, 'r', encoding='utf-8').read()

        chapter = epub.EpubHtml(
            title='Chapter ' + str(chapter_number),
            file_name=file
        )
        chapter.content = chapter_content
        chapter.add_item(default_css)

        book.add_item(chapter)
        chapters.append(chapter)
        toc.append(epub.Link(file, 'Chapter ' + str(chapter_number), 'chapter_' + str(chapter_number)))

    book.toc = tuple(toc)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = chapters

    epub.write_epub(out_epub, book, {})
    return out_epub