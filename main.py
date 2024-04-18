# external modules
import sys, json, pathlib, os, datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5 import QtCore


# internal modules
from MainGui import MainGui
import settings, helper_functions, easySQL, tables

def penumbra_path_validation(parent):
    """ This function is a preload warning if penumbra is not installed in the correct path which is
    usually an indication it isnt installed at all."""
    if not os.path.exists(settings.app_settings.get_setting('penumbra_path')):
        warning_dialog = QMessageBox(parent)
        warning_dialog.setWindowTitle('Incorrect Penumbra Installation...')
        warning_dialog.setText(f"""It appears that Penumbra is not installed on your system at: \n{app_settings.get_setting('penumbra_path')}\nThat means this program is useless to you at the moment! Please install Penumbra and follow its instructions before using this application!""")
        warning_dialog.setIcon(QMessageBox.Warning)
        warning_dialog.setStandardButtons(QMessageBox.Close)
        button = warning_dialog.exec()

        if button == QMessageBox.Close:
            sys.exit()

def build_and_update_collections_database():
    """  updates collections installed in the collections folder into the database """
    collections_folder = pathlib.Path(settings.app_settings.get_setting('penumbra_path')) / "Penumbra" / "collections"
    settings.app_settings.set_setting(key="collections_folder", value=str(collections_folder.absolute()))

    active_collections_json = pathlib.Path(settings.app_settings.get_setting('penumbra_path')) / "Penumbra" / "active_collections.json"
    settings.app_settings.set_setting(key="active_collections", value=str(active_collections_json.absolute()))

    active_collections = helper_functions.load_bom_json(active_collections_json)
    individuals = active_collections.pop("Individuals")
    active_collections.pop("Version")

    if os.path.isdir(collections_folder):
        for id, collection_json in enumerate(collections_folder.glob("*")):    
            data = helper_functions.load_bom_json(collection_json)
            character_links = {}
            
            for key, collection in active_collections.items():
                if collection == data['Name']:
                    character_links[key] = True
                else:
                    character_links[key] = False
            
            collection_indvi = []
            for individual in individuals:
                if individual['Collection'] == data['Name']:
                    collection_indvi.append(individual)
            
            character_links['Individuals'] = collection_indvi
            
            easySQL.insert_into_table(tables.collections, 
                (id,
                data['Version'],
                data['Name'],
                json.dumps(data['Settings']),
                json.dumps(data['Inheritance']),
                json.dumps(character_links)
                ))
            
            v = datetime.datetime.now().strftime("v%y.%m.%d")
            easySQL.insert_into_table(tables.metadata, (
                id,
                data['Name'],
                "Dummy Comment",
                str(v)
            ))

def build_and_update_modifications_database():
    """get the mod directory and updates into the modification database"""
    modification_folder = pathlib.Path(helper_functions.load_bom_json(pathlib.Path(settings.app_settings.get_setting('penumbra_path')) / "Penumbra.json")["ModDirectory"])
    settings.app_settings.set_setting(key="modification_folder", value=str(modification_folder.absolute()))

    if os.path.isdir(modification_folder):
         
         for id, modification in enumerate(modification_folder.glob("*")):
            try:
                meta_path = pathlib.Path(modification / "meta.json")
                if os.path.isdir(modification) and os.path.exists(meta_path):
                    length = 0
                    for file_path in modification.rglob("*"):
                        length += 1
                    
                    meta = helper_functions.load_bom_json(modification / "meta.json")
                    easySQL.insert_into_table(tables.modifications, (
                        id,
                        meta['FileVersion'],
                        meta['Name'],
                        meta['Author'],
                        meta['Description'],
                        meta['Version'],
                        meta['Website'],
                        json.dumps(meta['ModTags']),
                        str(modification.absolute()),
                        length
                    ))
                elif pathlib.Path(modification).suffix == ".pmp":
                    print(modification)
            except:
                print(modification)

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, False)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, False)


def main():
    app = QApplication(sys.argv)
    settings.app_settings.load_settings()
    main_gui = MainGui()
    
    # penumbra validation to ensure the plugin is even installed and set up!
    penumbra_path_validation(parent=main_gui)
    
    # build database
    build_and_update_collections_database()
    build_and_update_modifications_database()

    main_gui.__post__init__()
    main_gui.show()

    settings.app_settings.save_settings()

    sys.exit(app.exec_())

if __name__ == '__main__':
        main()    