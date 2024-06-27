from typing import List, Union

from books.models.manga import Manga
from books.models.lightnovel import Lightnovel
from books.models.ebook import Ebook
from cli import Cli, Separator

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

def books_menu(books: Union[List[Manga], List[Lightnovel], List[Ebook]], book_type: str):
    if book_type == "mangas":
        return mangas_menu(books)
    elif book_type == "lightnovels":
        return lightnovels_menu(books)
    else:
        return ebooks_menu(books)

def mangas_menu(mangas: List[Manga]):
    question = "==== MANGAS ===="
    choices = []

    for manga in mangas:
        entry = "{0:60.60}".format(manga.title) + 5 * " " + f"{manga.last_read_chapter}/{len(manga.chapters)}"
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No manga found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True)

def lightnovels_menu(lightnovels: List[Lightnovel]):
    question = "==== LIGHTNOVELS ===="
    choices = []

    for lightnovel in lightnovels:
        entry = {"name": "{0:60.60}".format(lightnovel.title) + 5 * " " + f"{lightnovel.last_read_chapter}/{len(lightnovel.chapters)}"}
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No lightnovel found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True)

def ebooks_menu(ebooks: List[Ebook]):
    question = "==== EBOOKS ===="
    choices = []

    for ebook in ebooks:
        read_status = "[READ]" if ebook.read else "[NOT READ]"
        entry = {"name": "{0:60.60}".format(ebook.title) + 5 * " " + f"{read_status}"}
        choices.append(entry)

    if not choices:
        question += "\n\n" + "No ebook found :("

    choices.extend([Separator(), "Back"])

    return Cli.select(question, choices, newline_after_question=True)

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