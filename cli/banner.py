import pyfiglet

from config import APPLICATION_NAME

def print_banner():
    ascii_banner = pyfiglet.figlet_format(APPLICATION_NAME)
    print(ascii_banner)