class Ebook():
    title: str
    read: bool
    missing: bool

    def __init__(self, title, read=False):
        self.title = title
        self.read = read
        self.missing = False