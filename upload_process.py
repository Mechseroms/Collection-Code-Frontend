"""
This file contains all Gui and logic directly impacting the exportation processing
"""
import httpx
import datetime
import os 
import json
import tempfile
import pathlib
from zipfile import ZIP_DEFLATED, ZipFile
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem, QProgressBar, QLabel, QPushButton
from PyQt5.QtGui import QIcon

import icons, settings

from cloud_backend import upload_file


global app_settings

app_settings = settings.app_settings


class UploadCollectionThread(QThread):
    """This thread logic takes a Penumbra Collection and compresses it into a .pcmp that can later be
    imported from another client. 

    Args:
        QThread (object): adjacent thread to main loop to allow for a progress indication for user QoL
    """
    
    next_step_signal = pyqtSignal(int) # tells progress bar what step it is on
    indicate_change = pyqtSignal(str) # used to change a label and return a string to said label
    set_progress_bar_max = pyqtSignal(int) # dynamic way to calculate total progress steps
    step_complete = pyqtSignal(int) # used to indicate in the progress dialog what steps are complete for QoL
    export_complete = pyqtSignal(bool) # used to indicate the Ui that it needs to repopulate
    
    def __init__(self, payload) -> None:
        super().__init__()
        self.payload = payload
        self.final_path = ""

    def run(self):
        """
        Main Thread logic that takes the provided collection and outputs a .pcmp file for use by the client.
        """

        collection_json = self.payload['collection_json']
        meta_json = self.payload['meta_data']

        #determine what mods to copy and total files
        total_files = self.calculate_total_files()
        meta_json['totalfiles'] = total_files  
        #send signals for progress and next step
        self.set_progress_bar_max.emit(total_files + 4)
        self.next_step_signal.emit(1)
        self.step_complete.emit(0)

        #create timestamp and temp folder for file path
        temporary_directory = tempfile.TemporaryDirectory()
        now = datetime.datetime.now()
        time_stamp = datetime.datetime.strftime(now, '%Y-%m-%d %H-%M')
        name = collection_json['Name']
        filename = f"{time_stamp}-{name}.pcmp"
        self.final_path = pathlib.Path(f"{temporary_directory.name}") / filename
        self.step_complete.emit(1)
        
        with ZipFile(self.final_path, 'w', compression=ZIP_DEFLATED) as pcmp_zip_file:
            self.next_step_signal.emit(2)
            self.copy_manifest_collection_data(
                pcmp_zip_file=pcmp_zip_file, 
                meta=meta_json, 
                collection_json=collection_json,
                temporary_directory=temporary_directory.name
                )
            
            self.step_complete.emit(2) 

            self.next_step_signal.emit(3)
            self.copy_modifications_to_zip(pcmp_zip_file=pcmp_zip_file)
            self.step_complete.emit(3) 

        
        self.upload_file(filename, self.final_path)
        self.step_complete.emit(4) 
        self.next_step_signal.emit(total_files + 4)
        temporary_directory.cleanup()
        self.export_complete.emit(True)

    def copy_modifications_to_zip(self, pcmp_zip_file: ZipFile):
        """ Overarching compression of each modification into the pcmp zip

        Args:
            zip_ref (zipfile.ZipFile): PenumbraCollection Modification Pack for exportation and importation
            mods_to_copy (list): A pre generated list of mod folders to compress into the .pcmp zip
        """
        overfile_files = 0

        for modification in self.payload['mods_to_copy']:
            zip_modification_final_path = os.path.join('mods', modification[0])
            local_modification_directory = pathlib.Path(modification[1])
            for current_file, file_path in enumerate(local_modification_directory.rglob("*")):
                pcmp_zip_file.write(file_path, arcname=os.path.join(zip_modification_final_path, file_path.relative_to(local_modification_directory)))
                overfile_files += 1
                self.indicate_change.emit(f"({current_file + 1}/{modification[2]}) Compressing {file_path} to zip...")
                self.next_step_signal.emit(3 + overfile_files)
            
    def calculate_total_files(self):
        """ Calculates the total files to copy into the .pcmp file

        Returns:
            total_files (int):
        """
        total_files = 0
        
        for modification in self.payload['mods_to_copy']:
            total_files += modification[2]
        return total_files
    
    def copy_manifest_collection_data(self, pcmp_zip_file: ZipFile, meta:dict, collection_json: dict, temporary_directory: str):
        """ Takes all the required files and data and writes them to the pcmp_zip_file

        Args:
            pcmp_zip_file (zipfile.ZipFile): PenumbraCollection Modification Pack for exportation and importation
            meta (dict): data needed for importation
            collection_json_path (str): Penumbra's generated json for the collection
        """
        # TODO: figure out how to save a file directly without having to use a temporary directory for it
        with open(os.path.join(temporary_directory, 'meta.json'), 'w') as file:
            json.dump(meta, file, indent=3)
        with open(os.path.join(temporary_directory, f"{collection_json['Id']}.json"), 'w') as file:
            json.dump(collection_json, file, indent=3)    
        pcmp_zip_file.write(os.path.join(temporary_directory, 'meta.json'), 'meta.json')
        pcmp_zip_file.write(os.path.join(temporary_directory, f"{collection_json['Id']}.json"), f"{collection_json['Id']}.json")

    def upload_file(self, filename, path):
        chunk_size = 10485760
        url = f"{settings.app_settings.connected_server}/upload_file"
        total = os.path.getsize(path)
        self.next_step_signal.emit(0)
        self.set_progress_bar_max.emit(total)
        self.indicate_change.emit(f"Uploading to {settings.app_settings.connected_server}...")
        data = {'filename': filename}
        total_chunks_transferred = 0
        with open(path, 'rb') as f:
            while (chunk := f.read(chunk_size)):
                files = {'file': (filename, chunk)}
                response = httpx.post(url, files=files, timeout=None)
                total_chunks_transferred += len(chunk)
                self.next_step_signal.emit(total_chunks_transferred)
                if response.status_code != 200:
                    break
        
        headers = {'Content-Type': 'application/json'}
        meta_data = self.payload['meta_data']
        collection_json = self.payload['collection_json']
        character_links = self.payload['character_links']
        mod_list = self.payload['mods_to_copy']
        data = {
            "username": settings.app_settings.username,
            "password": settings.app_settings.password,
            "filename": filename,
            "meta_data": meta_data,
            "collection_json": collection_json,
            "character_links": character_links,
            "mod_list": mod_list
        }

        response = httpx.post(f"{settings.app_settings.connected_server}/upload_info", headers=headers, json=data)
        print(response)

class UploadProgressDialog(QDialog):
    """PyQt5 dialog that displays a QoL checklist and progress bar for the end user during the exportation process.

    Args:
        QDialog (PyQt5.QtWidgets.QDialog):
    """
    export_steps = [
            "Organized environment for upload", 
            "Created manifest and collection information", 
            "Archive created and Collection and manifest copied",
            "Modifications copied",
            "Cleaning Up with Finishing Touches, Uploading",
            "Upload Done"
            ]
    
    def __init__(self, parent, payload):
        super().__init__(parent)

        self.payload = payload

        self.resize(400, 360)
        self.setWindowTitle('Uploading Collection...')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(10)

        self.QoL_step_label = QLabel(self)
        self.QoL_step_label.setWordWrap(True)

        self.QoL_step_list = QListWidget(self)
        self.abort_button = QPushButton(self)
        self.abort_button.setText("Abort")
        
        self.QoL_step_label.setGeometry(30, 25, 340, 25)
        self.progress_bar.setGeometry(30, 60, 340, 25)
        self.QoL_step_list.setGeometry(30, 95, 340, 215)
        self.abort_button.setGeometry(310, 325, 80, 25)

        
        for each in self.export_steps:
            item = QListWidgetItem()
            item.setIcon(QIcon(icons.step_incomplete))
            item.setText(each)
            self.QoL_step_list.addItem(item)
        
        self.final_path = ""


        self.show()

    def start_upload(self):
        self.my_thread = UploadCollectionThread(payload=self.payload)
        self.my_thread.next_step_signal.connect(self.onStepChange)
        self.my_thread.indicate_change.connect(self.onLabelChange)
        self.my_thread.set_progress_bar_max.connect(self.set_dynamic_maximum)
        self.my_thread.step_complete.connect(self.stepComplete)
        self.my_thread.start()

    def onStepChange(self, value):
        self.progress_bar.setValue(value)

    def onLabelChange(self, text):
        self.QoL_step_label.setText(text)
        
    def set_dynamic_maximum(self, value):
        self.progress_bar.setMaximum(value)
        
    def abort_upload(self):
        # TODO: abort logic requires that the ZIP be deleted so there is no confusion on a half baked modpack
        pass
    
    def close(self) -> bool:
        self.final_path = self.my_thread.final_path
        self.my_thread.exit()
        return super().close()
    
    def stepComplete(self, index):
        self.QoL_step_list.item(index).setIcon(QIcon(icons.step_complete))
        if index == 4:
            self.QoL_step_list.item(4).setIcon(QIcon(icons.step_complete))
            self.QoL_step_list.item(5).setIcon(QIcon(icons.step_complete))
            self.abort_button.setText('Done')
            self.abort_button.clicked.connect(self.close)
        else:
            self.QoL_step_list.item(index).setIcon(QIcon(icons.step_complete))