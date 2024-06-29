from typing import List, Callable
import beaupy
from rich.console import Console
import os

from cli.banner import print_banner

class Cli:

    @classmethod
    def prettyfy(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print_banner()

    @classmethod
    def confirm(self, question: str):
        self.prettyfy()
        return beaupy.confirm(question)
    
    @classmethod
    def prompt(self, question: str, target_type: type = str, validator: Callable = None, failed_validator_msg: str = ""):
        if not validator:
            self.prettyfy()
            return beaupy.prompt(question, target_type=target_type) 
            
        else:
            validated = False
            while not validated:
                self.prettyfy()
                try:
                    value = beaupy.prompt(question, target_type=target_type, validator=validator)
                    validated = True
                except beaupy.ValidationError:
                    input(failed_validator_msg)

            return value
    
    @classmethod
    def select(self, question: str, choices: List[str], cursor: str = "🢧", cursor_style: str = "pink1", pagination: bool = False, page_size: int = 5, newline_after_question: bool = False):
        # First we remove every Separator instances and instead add a space to the line before... that's a quick hack because beaupy doesn't support newlines :(
        for idx, choice in enumerate(choices):
            if isinstance(choice, Separator):
                if idx > 0:
                    choices[idx - 1] += "\n"
                choices.pop(idx)

        self.prettyfy()
        
        Console().print(question) if not newline_after_question else Console().print(question + "\n")
        choice = beaupy.select(choices, cursor=cursor, cursor_style=cursor_style, pagination=pagination, page_size=page_size)

        # Again doing this as an odd hack to be able to add newlines in the choices...
        if type(choice) == str:
            choice = choice.strip()

        return choice

    @classmethod
    def print(self, text: str, end='\n'):
        self.prettyfy()
        print(text, end=end)


class Separator:

    def __init__(self):
        pass