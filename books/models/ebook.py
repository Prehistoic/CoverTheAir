class Ebook():
    title: str
    series: str
    read: bool
    filetype: str
    missing: bool

    def __init__(self, title: str, series: str, read: bool =False, filetype: str = "epub"):
        self.title = title
        self.series = series
        self.read = read
        self.filetype = filetype
        self.missing = False