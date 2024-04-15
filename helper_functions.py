import json, pathlib

""" Here i will be putting any helper functions that may be used throughout
the application in order to not have to write the same code at the same time. """

def load_bom_json(file_path: pathlib.Path) -> json:
    """ helper function to encode a json as utf-8 and then load it returning the dict. """
    with file_path.open(encoding="utf-8-sig") as loaded_file:
        return json.load(loaded_file)