from typing import List
import re

class Manga():
    title: str
    source: str
    chapters: List[str]
    last_read_chapter: int
    missing: bool

    def __init__(self, title, source, chapters=[], last_read_chapter=0):
        self.title = title
        self.source = source
        self.chapters = chapters
        self.last_read_chapter = last_read_chapter
        self.missing = False

    def update_chapters(self, up_to_date_chapters: List[str]):
        # Track the chapter at the current last_read_chapter index
        current_last_read_chapter = self.chapters[self.last_read_chapter - 1] if self.last_read_chapter != 0 else 0
        
        # Find new chapters in up_to_date_chapters that are not in current chapters
        new_chapters = list(set(up_to_date_chapters) - set(self.chapters))

        # We add missing chapters to the ones we already have
        self.chapters = list(set(up_to_date_chapters) | set(self.chapters))

        # Sorting chapters
        chapter_re = re.compile(r'.*? (\d+(\.\d+)?)\.cbz')
        new_chapters = sorted(new_chapters, key=lambda f: float(chapter_re.search(f).group(1)))
        self.chapters = sorted(self.chapters, key=lambda f: float(chapter_re.search(f).group(1)))
        
        # Update last_read_chapter to point to the new index of the previous last_read_chapter
        self.last_read_chapter = self.chapters.index(current_last_read_chapter) + 1 if current_last_read_chapter != 0 else 0

        return new_chapters