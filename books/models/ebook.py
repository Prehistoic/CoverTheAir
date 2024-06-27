class Ebook():
    title: str
    read: bool
    filetype: str
    missing: bool

    def __init__(self, title: str, read: bool =False, filetype: str = "epub"):
        self.title = title
        self.read = read
        self.filetype = filetype
        self.missing = False