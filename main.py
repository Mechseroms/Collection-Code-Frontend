# external modules
import sys, json, pathlib, os, datetime, requests, tempfile, zipfile, subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5 import QtCore
from cloud_backend import UpdateOptInDialog, ping


# internal modules
from MainGui import MainGui
import settings, helper_functions, easySQL, tables

def penumbra_path_validation(parent):
    """ This function is a preload warning if penumbra is not installed in the correct path which is
    usually an indication it isnt installed at all."""
    if not os.path.exists(settings.app_settings.get_setting('penumbra_path')):
        warning_dialog = QMessageBox(parent)
        warning_dialog.setWindowTitle('Incorrect Penumbra Installation...')
        warning_dialog.setText(f"""It appears that Penumbra is not installed on your system at: \n{settings.app_settings.get_setting('penumbra_path')}\nThat means this program is useless to you at the moment! Please install Penumbra and follow its instructions before using this application!""")
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
            file_extension = os.path.splitext(collection_json)[1]
            if file_extension == ".json":
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
                    data['Id'],
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
    settings.app_settings.external_path = pathlib.Path.cwd()

    main_gui = MainGui()
    
    if settings.app_settings.first_load:
        dialog = UpdateOptInDialog(main_gui, "https://ffxiv.treehousefullofstars.com/update_app/latest")
        result = dialog.exec()
        if result == 1:
            settings.app_settings.set_setting("update_opt_in", dialog.get_opt_in_state())
            settings.app_settings.set_setting("update_pipeline", dialog.get_pipeline())
            settings.app_settings.save_settings()
        else:
            return False


    if settings.app_settings.get_setting("update_opt_in"):
        pipeline = settings.app_settings.get_setting("update_pipeline")
        app_version = settings.app_settings.get_setting("app_version")
        url_break = pipeline.split("/")
        url = url_break[0] + "//" + url_break[2] + "/check_server"
        result = ping(url)
        if result:
            update_info = requests.get(str(pipeline + "/" + app_version)).json()['data']
        
        print(update_info['update_ready'])
        if update_info['update_ready']:
            msg_box_name = QMessageBox()
            msg_box_name.setIcon(QMessageBox.Question)
            msg_box_name.setWindowTitle("Update Available...")
            msg_box_name.setText(f"It appears there is an update to the app available.\n\nYour current version is: {app_version}\nThe new version is: {update_info['latest_version']}\n\nPlease update your app, if you decline to then your ability to connect to servers will be disabled!") 
            msg_box_name.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
            retval = msg_box_name.exec_()

            if retval == QMessageBox.No:
                settings.app_settings.lock_client = True

            if retval == QMessageBox.Ok:
                return False

    # penumbra validation to ensure the plugin is even installed and set up!
    penumbra_path_validation(parent=main_gui)
    
    # build database
    build_and_update_collections_database()
    build_and_update_modifications_database()

    main_gui.__post__init__()
    main_gui.show()

    settings.app_settings.save_settings()

    avatars = pathlib.Path(settings.app_settings.external_path.absolute()) / "avatars"
    avatars.mkdir(parents=True, exist_ok=True)
    sys.exit(app.exec_())

if __name__ == '__main__':
    print(sys.argv)
    try: 
        main()
        sys.exit()
    except Exception as e:
        with open('log.txt', "w+") as file:
            file.write(str(e))