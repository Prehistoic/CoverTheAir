import os
import zipfile
import traceback

from utils.log import Log

class Cbz:
    
    path: str

    def __init__(self, path: str):
        self.path = path

    def unzip(self):
        try:
            # Extract the directory path and file name
            directory_path = os.path.dirname(self.path)
            file_name = os.path.basename(self.path)
            
            # Remove the .cbz extension from the file name
            file_base_name = os.path.splitext(file_name)[0]
            
            # Create a directory named after the file (without the .cbz extension)
            output_directory = os.path.join(directory_path, file_base_name)
            os.makedirs(output_directory, exist_ok=True)
            
            # Unzip the .cbz file into the output directory
            with zipfile.ZipFile(self.path, 'r') as zip_ref:
                zip_ref.extractall(output_directory)

            Log.debug(f"Unzipped {self.path} successfully")
            return output_directory
        except Exception:
            Log.debug(f"Failed to unzip {self.path}", traceback.format_exc())
            return None