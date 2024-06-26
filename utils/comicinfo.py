import xml.etree.ElementTree as ET
import traceback

from utils.log import Log

class ComicInfo:

    path: str
    data: ET.Element = None

    def __init__(self, path: str):
        try:
            self.path = path

            with open(path, "r") as f:
                content = f.read()
                self.data = ET.fromstring(content)
        except Exception:
            Log.error(f"Failed to parse {path} as a ComicInfo.xml file", traceback.format_exc())

    def get_writer(self):
        try:
            return self.data.find('Writer').text
        except:
            Log.warning(f"Couldn't find Writer in provided ComicInfo.xml ({self.path})")
            return ""