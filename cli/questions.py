from typing import List, Union
from PyInquirer import Separator
from books.models.manga import Manga
from books.models.lightnovel import Lightnovel
from books.models.ebook import Ebook

main_menu_question = [
    {
        'type': 'list',
        'name': 'main_menu',
        'message': 'Which type of books do you want to see ?',
        'choices': [
            Separator(' '),
            'Mangas',
            'Lightnovels',
            'Ebooks',
            Separator(' '),
            'Quit CoverTheAir'
        ]
    }
]

def generate_books_menu(books: Union[List[Manga], List[Lightnovel], List[Ebook]], book_type: str):
    if book_type == "mangas":
        choices = generate_mangas_choices(books)
    elif book_type == "lightnovels":
        choices = generate_lightnovels_choices(books)
    else:
        choices = generate_ebooks_choices(books)

    question = [
        {
            'type': 'list',
            'name': 'books_menu',
            'message': '==== MANGAS ====',
            'choices' : [Separator(' ')] + choices + [Separator(' '), 'Back']
        }
    ]
    return question

def generate_mangas_choices(mangas: List[Manga]):
    choices = []

    for manga in mangas:
        entry = {"name": "{0:60.60}".format(manga.title) + 5 * " " + f"{manga.last_read_chapter}/{len(manga.chapters)}"}
        choices.append(entry)
    
    if not choices:
        return ["No manga found :("]

    return choices

def generate_lightnovels_choices(lightnovels: List[Lightnovel]):
    choices = []

    for lightnovel in lightnovels:
        entry = {"name": "{0:60.60}".format(lightnovel.title) + 5 * " " + f"{lightnovel.last_read_chapter}/{len(lightnovel.chapters)}"}
        choices.append(entry)

    if not choices:
        return ["No lightnovel found :("]

    return choices

def generate_ebooks_choices(ebooks: List[Ebook]):
    return []

chosen_manga_or_lightnovel_question = [
    {
        'type': 'list',
        'name': 'chosen_book',
        'message': 'What do you want to do ?',
        'choices': [
            'Upload new chapters to Ebook Reader',
            'Modify last chapter read',
            Separator(' '),
            'Back'
        ]
    }
]

chosen_ebook_question = [
    {
        'type': 'list',
        'name': 'chosen_book',
        'message': 'What do you want to do ?',
        'choices': [
            'Upload to Ebook Reader',
            'Modify read status',
            Separator(' '),
            'Back'
        ]
    }
]

def generate_modify_last_chapter_read_question(book: Union[Manga, Lightnovel]):
    modify_last_chapter_read_question = [
        {
            'type': 'input',
            'name': 'modify_last_chapter_read',
            'message': f"What\'s the last chapter you read (current one saved is {book.last_read_chapter})",
            'validate': lambda val: True if val.isnumeric() and int(val) >= 0 and int(val) <= len(book.chapters) else f"Must choose an integer between 0 and {len(book.chapters)}"
        }
    ]
    return modify_last_chapter_read_question

read_status_question = [
    {
        'type': 'list',
        'name': 'read_status',
        'message': 'Have you read this book ?',
        'choices': ['Yes', 'No']
    }
]

def generate_chapters_download_count_question(book: Union[Manga, Lightnovel]):
    if book.last_read_chapter == len(book.chapters):
        return None

    unread_chapters_count = len(book.chapters) - book.last_read_chapter

    message = "{} => Still {} chapters to read ! How many should I download ?".format(book.title, unread_chapters_count)

    possible_choices = [5, 10, 20, 30, 50, 100]
    choices = [unread_chapters_count]
    for choice in possible_choices:
        if choice < unread_chapters_count:
            choices.append(choice)
    choices = [str(choice) for choice in sorted(choices)] + [Separator(' '), "Back"]

    chapters_download_count_question = [
        {
            'type': 'list',
            'name': 'chapters_download_count',
            'message': message,
            'choices': choices
        }
    ]
    return chapters_download_count_question