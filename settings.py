import json, os, pathlib

class AppSettings(object):
    def __init__(self, path) -> None:
        self.path = pathlib.Path(path)
        self.__get__ = {}
        self.username = ""
        self.password = ""
        self.connected_server = ""
        self.port = ""
        self.user_data = {}
        self.connected = False
        self.external_path = ""
        self.update_opt_in = False
        self.update_pipeline = ""
        self.first_load = False
        self.app_version = ""
        self.lock_client = False

    def get_setting(self, key=None):
        """ getter for any key in the settings dictionary! call it without a provided key to get the whole dictionary or pass a
            key value and it returns that settings.
        """
        if key:
            return self.__get__[key]
        return self.__get__
    
    def set_setting(self, key, value):
        """ setter for any value in the settings """
        self.__get__[key] = value
    
    def load_settings(self):
        """ This loads pre-existing settings or the default if none exists! """
        # check if settings exists if does then load that into variable
        if os.path.exists(self.path.absolute()):
            with self.path.open('r+') as file:
                file_contents = json.load(file)
                self.__get__ = file_contents
                self.first_load = False
                self.lock_client = False
        # if not then create it and load in defaults
        else:
            global default_settings
            with self.path.open('w+') as file:
                json.dump(default_settings, file)
            self.__get__ = default_settings
            self.first_load = True

    def save_settings(self):
        """ Saves the current settings values to self.path! """
        # check to see if the path exists for failsafe and then write to json
        if os.path.exists(self.path.absolute()):
            with self.path.open('w+') as file:
                json.dump(self.__get__, file, indent=2)



global app_settings 
app_settings = AppSettings('settings.json')

global default_settings
default_settings = {
    "window_title": "Collection Sharing App",
    "window_height": 400,
    "window_width": 640,
    "penumbra_path": str(pathlib.Path(pathlib.Path.home() / "AppData/Roaming" / "XIVLauncher" / "pluginConfigs").absolute()),
    "advanced_mode": False,
    "update_opt_in": False,
    "update_pipeline": "",
    "app_version": "alpha_v1.0"
}