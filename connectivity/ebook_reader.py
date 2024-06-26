import traceback
import paramiko
import os
from rich.progress import Progress

from config import EBOOK_READER_IP, EBOOK_READER_PORT, EBOOK_READER_PKEY_FILE, EBOOK_READER_USERNAME, EBOOK_READER_BASE_PATH
from cli.prettyfy import pprint
from utils.log import Log

class EbookReader:

    transport = None
    sftp = None

    def connect(self):
        try:
            Log.info(f"Connecting to ebook reader: {EBOOK_READER_USERNAME}@{EBOOK_READER_IP}:{EBOOK_READER_PORT} with key {EBOOK_READER_PKEY_FILE}")

            self.transport = paramiko.Transport((EBOOK_READER_IP,EBOOK_READER_PORT), disabled_algorithms={'pubkeys':['rsa-sha2-512', 'rsa-sha2-256']})
            self.transport.connect(username=EBOOK_READER_USERNAME, pkey=paramiko.RSAKey.from_private_key_file(EBOOK_READER_PKEY_FILE))
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)

            Log.info("Connection successful")
        except:
            Log.error("Failed to connect to ebook reader", traceback.format_exc())

    def disconnect(self):
        try:
            Log.info(f"Disconnecting from ebook reader : {EBOOK_READER_USERNAME}@{EBOOK_READER_IP}:{EBOOK_READER_PORT}")

            self.sftp = self.sftp.close()
            self.transport = self.transport.close()

            Log.info("Disconnection successful")
        except:
            Log.error("Failed to disconnect from ebook reader", traceback.format_exc())

    def put(self, source_path: str, target_path: str):
        try:
            with Progress() as progress:
                progress_bar_length = os.path.getsize(source_path)
                task = progress.add_task(f"[red]Uploading {os.path.basename(source_path)} to Ebook Reader", total=progress_bar_length)

                # Define a callback for updating progress
                def progress_callback(transferred, total):
                    progress.update(task, completed=transferred)

                self.sftp.put(source_path, target_path, callback=progress_callback)
                Log.debug(f"SFTP PUT {source_path} (HOST) => {target_path} (SERVER)")
                return True
        except Exception:
            Log.error(f"SFTP PUT {source_path} (HOST) => {target_path} (SERVER)", traceback.format_exc())
            return False

    def get(self, source_path: str, target_path: str):
        try:
            with Progress() as progress:
                progress_bar_length = self.sftp.stat(source_path).st_size
                task = progress.add_task(f"[red]Downloading {source_path} from Ebook Reader", total=progress_bar_length)

                # Define a callback for updating progress
                def progress_callback(transferred, total):
                    progress.update(task, completed=transferred)

                self.sftp.get(source_path, target_path, callback=progress_callback)
                Log.debug(f"SFTP GET {source_path} (SERVER) => {target_path} (HOST)")
                return True
        except Exception:
            Log.error(f"SFTP GET {source_path} (SERVER) => {target_path} (HOST)", traceback.format_exc())
            return False

    def upload_book(self, book_title: str, source_path: str):
        upload_success = False

        if self.sftp:
            target_path = EBOOK_READER_BASE_PATH + "/" + book_title.replace(" ","_") + ".epub"
            upload_success = self.put(source_path, target_path)

        return upload_success

    def retrieve_book(self, book_title: str, target_path: str):
        retrieval_success = False

        if self.sftp:
            source_path = EBOOK_READER_BASE_PATH + "/" + book_title.replace(" ","_") + ".epub"
            retrieval_success = self.get(source_path, target_path)

        return retrieval_success
    

