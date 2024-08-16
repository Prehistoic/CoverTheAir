from typing import List, Union
import os

from books.models.manga import Manga
from books.models.lightnovel import Lightnovel
from books.models.ebook import Ebook
from cli import Cli, Separator
from config import SUPPORTED_EBOOK_FORMATS, LOCAL_UPLOADS_DIR

def main_menu():
    question = "Which type of books do you want to see ?"
    choices = [
        "Mangas",
        "Lightnovels",
        "Ebooks",
        Separator(),
        "Quit CoverTheAir"
    ]

    return Cli.select(question, choices, newline_after_question=True)

def choose_manga(mangas: List[Manga]):
    question = "==== MANGAS ===="
    choices = []

    for manga in mangas:
        entry = "{0:60.60}".format(manga.title) + 5 * " " + f"{manga.last_read_chapter}/{len(manga.chapters)}"
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No manga found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True)

def choose_lightnovel(lightnovels: List[Lightnovel]):
    question = "==== LIGHTNOVELS ===="
    choices = []

    for lightnovel in lightnovels:
        entry = "{0:60.60}".format(lightnovel.title) + 5 * " " + f"{lightnovel.last_read_chapter}/{len(lightnovel.chapters)}"
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No lightnovel found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True)

def choose_series(ebooks: List[Ebook]):
    question = "==== SERIES ===="
    choices = []

    available_series = {}
    for ebook in ebooks:
        if ebook.series not in available_series:
            available_series[ebook.series] = [ebook]
        else:
            available_series[ebook.series].append(ebook)

    for serie in available_series.keys():
        entry = "{0:60.60}".format(serie)
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No series found :("

    choices.extend([Separator(), "Upload local ebook to Media Server", Separator(), "Back"])

    return available_series, Cli.select(question, choices, newline_after_question=True, pagination=True, page_size=20)

def choose_ebook(serie: str, ebooks: List[Ebook]):
    question = f"==== {serie.upper()} ===="
    choices = []

    for ebook in ebooks:
        read_status = "[READ]" if ebook.read else "[NOT READ]"
        entry = "{0:60.60}".format(ebook.title) + 5 * " " + f"{read_status}"
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No ebook found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True, pagination=True, page_size=20)

def choose_action_for_manga_or_lightnovel():
    question = "What do you want to do ?"
    choices = [
        "Upload new chapters to Ebook Reader",
        "Modify last chapter read",
        Separator(),
        "Back"
    ]

    return Cli.select(question, choices, newline_after_question=True)

def choose_action_for_ebook():
    question = "What do you want to do ?"
    choices = [
        "Upload to Ebook Reader",
        "Modify read status",
        Separator(),
        "Back"
    ]

    return Cli.select(question, choices, newline_after_question=True)

def choose_local_ebook_to_upload():
    question = f"Please provide the name of the ebook to upload\nWARNING : it has to be in {LOCAL_UPLOADS_DIR}"
    validator = lambda f: os.path.isfile(os.path.join(LOCAL_UPLOADS_DIR, f)) and f.split(".")[-1] in SUPPORTED_EBOOK_FORMATS
    failed_validator_msg = "Provided path is not a valid ebook !"
    
    ebook_file = Cli.prompt(question, validator=validator, failed_validator_msg=failed_validator_msg)
    return os.path.join(LOCAL_UPLOADS_DIR, ebook_file) if ebook_file else None

def input_serie():
    question = f"Please provide the name of the series this book belongs to"
    return Cli.prompt(question)

def modify_last_chapter_read(book: Union[Manga, Lightnovel]):
    question = f"What\'s the last chapter you read (current one saved is {book.last_read_chapter})"
    validator = lambda val: 0 <= val <= len(book.chapters)
    failed_validator_msg = f"Must choose an integer between 0 and {len(book.chapters)}"
    return Cli.prompt(question, target_type=int, validator=validator, failed_validator_msg=failed_validator_msg)

def modify_read_status(book: Ebook):
    question = f"Have you finished reading {book.title} ?"
    return Cli.confirm(question)

def get_chapters_download_count(book: Union[Manga, Lightnovel]):
    if book.last_read_chapter == len(book.chapters):
        return Cli.select("You have already read every chapter !", ["Back"], newline_after_question=True)
    
    unread_chapters_count = len(book.chapters) - book.last_read_chapter

    question = "{} => Still {} chapters to read ! How many should I download ?".format(book.title, unread_chapters_count)

    possible_choices = [5, 10, 20, 30, 50, 100]
    choices = [unread_chapters_count]
    for choice in possible_choices:
        if choice < unread_chapters_count:
            choices.append(choice)
    choices = [str(choice) for choice in sorted(choices)] + [Separator(), "Back"]

    return Cli.select(question, choices, newline_after_question=True)