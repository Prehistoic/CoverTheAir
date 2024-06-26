from typing import List
from PyInquirer import prompt
import os

from cli.banner import print_banner

def pprompt(question: List):
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    return prompt(question)

def pprint(text: str, end='\n'):
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    print(text, end=end)

