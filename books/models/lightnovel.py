from typing import List

class Lightnovel():
    title: str
    chapters: List[str]
    last_read_chapter: int
    missing: bool

    def __init__(self, title, chapters=[], last_read_chapter=0):
        self.title = title
        self.chapters = chapters
        self.last_read_chapter = last_read_chapter
        self.missing = False