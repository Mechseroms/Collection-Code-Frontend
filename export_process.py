"""
This file contains all Gui and logic directly impacting the exportation processing
"""
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

import icons, settings, easySQL, tables


global app_settings

app_settings = settings.app_settings


class ExportCollectionThread(QThread):
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

        #create timestamp and file path
        now = datetime.datetime.now()
        time_stamp = datetime.datetime.strftime(now, '%Y-%m-%d %H-%M')
        name = collection_json['Name']
        final_path = pathlib.Path(f"{self.payload['save_directory']}") / f"{time_stamp}-{name}.pcmp"
        self.step_complete.emit(1)
        with ZipFile(final_path, 'w', compression=ZIP_DEFLATED) as pcmp_zip_file:
            self.next_step_signal.emit(2)
            self.copy_manifest_collection_data(
                pcmp_zip_file=pcmp_zip_file, 
                meta=meta_json, 
                collection_json=collection_json
                )
            self.step_complete.emit(2) 

            self.next_step_signal.emit(3)
            self.copy_modifications_to_zip(pcmp_zip_file=pcmp_zip_file)
            self.step_complete.emit(3) 


        self.step_complete.emit(4) 
        self.next_step_signal.emit(total_files + 4)
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
    
    def copy_manifest_collection_data(self, pcmp_zip_file: ZipFile, meta:dict, collection_json: dict):
        """ Takes all the required files and data and writes them to the pcmp_zip_file

        Args:
            pcmp_zip_file (zipfile.ZipFile): PenumbraCollection Modification Pack for exportation and importation
            meta (dict): data needed for importation
            collection_json_path (str): Penumbra's generated json for the collection
        """
        # TODO: figure out how to save a file directly without having to use a temporary directory for it
        temporary_directory = tempfile.TemporaryDirectory()
        with open(os.path.join(temporary_directory.name, 'meta.json'), 'w') as file:
            json.dump(meta, file, indent=3)
        with open(os.path.join(temporary_directory.name, f"{collection_json['Name']}.json"), 'w') as file:
            json.dump(collection_json, file, indent=3)    
        pcmp_zip_file.write(os.path.join(temporary_directory.name, 'meta.json'), 'meta.json')
        pcmp_zip_file.write(os.path.join(temporary_directory.name, f"{collection_json['Name']}.json"), f"{collection_json['Name']}.json")
        temporary_directory.cleanup()



class ExportProgressDialog(QDialog):
    """PyQt5 dialog that displays a QoL checklist and progress bar for the end user during the exportation process.

    Args:
        QDialog (PyQt5.QtWidgets.QDialog):
    """
    export_steps = [
            "Organized environment for export", 
            "Created manifest, paths, collection information", 
            "Archive created and Collection and manifest copied",
            "Modifications copied",
            "Cleaning Up with Finishing Touches",
            "Export Done"
            ]
    
    def __init__(self, parent, payload):
        super().__init__(parent)

        self.payload = payload

        self.resize(400, 360)
        self.setWindowTitle('Exporting Collection...')
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
        
        self.show()

    def start_exportation(self):
        self.my_thread = ExportCollectionThread(payload=self.payload)
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
        
    def abort_export(self):
        # TODO: abort logic requires that the ZIP be deleted so there is no confusion on a half baked modpack
        pass
    
    def close(self) -> bool:
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