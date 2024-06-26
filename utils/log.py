import logging

from config import LOGFILE, LOG_LEVEL

# We re-create the logfile at each execution (to avoid infinite logfile)
with open(LOGFILE, "w") as f: pass

# We set up the logging globally
level = getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)
logging.basicConfig(filename=LOGFILE, filemode='a', format='%(levelname)s: %(message)s', level=level)
logging.getLogger('paramiko.transport').setLevel(logging.ERROR)

class Log:
    @classmethod
    def info(self, msg: str):
        logging.info(msg)

    @classmethod
    def debug(self, msg: str):
        logging.debug(msg)

    @classmethod
    def warning(self, msg: str):
        logging.warning(msg)

    @classmethod
    def error(self, msg: str, stacktrace: str):
        logging.error(msg + "\n\n" + stacktrace)