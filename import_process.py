from PyQt5.QtWidgets import (QDialog, QProgressBar, QLabel, QListWidget, QPushButton, QListWidgetItem)
from PyQt5.QtGui import QIcon
import json, zipfile, pathlib, shutil, os
from PyQt5.QtCore import QThread, pyqtSignal
import icons, settings, helper_functions

global app_settings
app_settings = settings.app_settings

class ImportCollectionThread(QThread):
    """This Thread logic takes a Penumbra Collection ModPack (.pcmp) and decompresses it into the users Modification
    and collection folders. 

    Args:
        QThread (object): adjacent thread to main loop to allow for a progress indication for user QoL
    """
    next_step_signal = pyqtSignal(int) # tells progress bar what step it is on
    indicate_change = pyqtSignal(str) # used to change a label and return a string to said label
    set_progress_bar_max = pyqtSignal(int) # dynamic way to calculate total progress steps
    step_complete = pyqtSignal(int) # used to indicate in the progress dialog what steps are complete for QoL
    
    def __init__(self, payload):
        """
        Args:
            path_to_pcmp (str):
            user_collection_directory (str):
            user_modification_directory (str):
        """
        super().__init__()
        self.payload = payload
        
    def run(self):
        
        self.collection_name = self.payload['meta_data']['collection_name']
        #save collection
        collections_folder = pathlib.Path(app_settings.get_setting('collections_folder'))
        collection_path = collections_folder / f"{self.collection_name}.json"
        
        
        # need to modify collection json for unique tag...
        collection_settings = self.payload['collection_json']['Settings']
        new_settings = {}
        for key, value in collection_settings.items():
            new_settings[f"({self.collection_name}) {key}"] = value
        self.payload['collection_json']['Settings'] = new_settings
        
        
        with collection_path.open('w+') as file:
            try:
                json.dump(self.payload['collection_json'], file, indent=2)
            except TypeError as e:
                print(e)
        
        sort_order_json = pathlib.Path(app_settings.get_setting('penumbra_path'), f"Penumbra/sort_order.json")
        print(sort_order_json)
        sort_order = helper_functions.load_bom_json(sort_order_json)
        sort_order_data = sort_order['Data']

        self.step_complete.emit(0) # copy over collection data signal
        self.set_progress_bar_max.emit(self.payload['meta_data']['totalfiles'])
        # TODO: create a database to save what collections are imported.

        with zipfile.ZipFile(self.payload['path_to_zip']) as pcmp_file:
            self.step_complete.emit(1) # open zip folder and set up environment signal
            # copy mods into mod folder
            name_list = pcmp_file.namelist()
            overcount_files = 0
            for modification in self.payload['mods_to_copy']:
                sort_order_data[f"({self.collection_name}) {modification}"] = f"{self.collection_name}/({self.collection_name}) {modification}"
                #makes all mod folders unique by default TODO: replace mod_folder_test with user folder
                
                # Determine modifactions target directory and make sure it does not exists
                modification_folder = pathlib.Path(app_settings.get_setting("modification_folder"), f"({self.collection_name}) {modification}")
                if not os.path.exists(modification_folder):
                    os.mkdir(modification_folder)

                # Create a filtered lists of all the found paths in the archives mods folder
                filtered_paths_to_copy = [path for path in name_list if f"mods/{modification}" in path]
                
                file_paths = [] # stores file paths and name for indexing and saving an index in the mods folder for future use.
                
                # Start the counter and copying each filtered file in the archive over to the modification target
                for current_count, path in enumerate(filtered_paths_to_copy):
                    
                    target_path = modification_folder / path.replace(f"mods/{modification}/", "")
                    file_paths.append(tuple([path, str(target_path)]))
                    
                    member_info = pcmp_file.getinfo(path)
                    
                    # if the path is a inner directory then make it else, copy the file over into the target_path
                    if member_info.is_dir():
                        try:
                            os.makedirs(target_path)
                        except FileExistsError as e:
                            #print(e)
                            pass
                    elif "meta.json" in path:
                        data = json.load(pcmp_file.open(path))
                        data['Name'] = f"({self.collection_name}) {data['Name']}"
                        with target_path.open("w+") as _file:
                            json.dump(data, _file, indent=2)
                    else:
                        source = pcmp_file.open(path) # path into the archive
                        target = open(target_path, 'wb+') # target path on the local machine
                        with source, target_path:
                            shutil.copyfileobj(source, target)
                        target.close()
                    
                    overcount_files += 1
                    self.indicate_change.emit(f"({current_count}/{len(filtered_paths_to_copy)}) decompressing {path} to {modification_folder}...")
                    self.next_step_signal.emit(overcount_files)
                    
                # Save a files index into the modifications folder
                files_index_json = modification_folder / "pcmp_index.json"
                with files_index_json.open('w+') as index_file:
                    json.dump(file_paths, index_file, indent=2)

        sort_order['Data'] = sort_order_data

        with sort_order_json.open('w+') as _file:
            json.dump(sort_order, _file, indent=2)

        self.step_complete.emit(2) # Modifications copied signal
        self.step_complete.emit(3) # clean up and closing files signal
        self.step_complete.emit(4) # import done

class ImportProgressDialog(QDialog):    
    steps = [
            "Opened Archive",
            "Copying Collection files",
            "Modifications Copied",
            "Cleaning Up with Finishing Touches",
            "Import Done"
            ]
    
    def __init__(self, parent, payload):
        super().__init__(parent)

        self.payload = payload

        self.resize(400, 360)
        self.setWindowTitle('Importing Collection...')
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

        
        for each in self.steps:
            item = QListWidgetItem()
            item.setIcon(QIcon(icons.step_incomplete))
            item.setText(each)
            self.QoL_step_list.addItem(item)
        
        self.show()

    def import_collection(self):
        """ main function that leads into the import thread.

        Args:
            path_to_pcmp (str): pcmp file to import
        """
        # TODO: I want to be able to manipulate this data
        self.my_thread = ImportCollectionThread(payload=self.payload)
        self.my_thread.next_step_signal.connect(self.do_step_change)
        self.my_thread.indicate_change.connect(self.change_label)
        self.my_thread.set_progress_bar_max.connect(self.set_Progress_Bar_max)
        self.my_thread.step_complete.connect(self.step_complete)
        self.my_thread.start()

    def do_step_change(self, progress_value: int):
        self.progress_bar.setValue(progress_value)

    def change_label(self, text: str):
        self.QoL_step_label.setText(text)
        
    def set_Progress_Bar_max(self, progress_max: int):
        self.progress_bar.setMaximum(progress_max)
    
    def abort_import(self):
        pass

    def done_button(self):
        self.my_thread.exit()
        return super().close()

    def step_complete(self, index):
        if index == 3:
            self.QoL_step_list.item(3).setIcon(QIcon(icons.step_complete))
            self.QoL_step_list.item(4).setIcon(QIcon(icons.step_complete))
            self.abort_button.setText('Done')
            self.abort_button.clicked.connect(self.done_button)
        else:
            self.QoL_step_list.item(index).setIcon(QIcon(icons.step_complete))