import sys, os
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
    

icon_dir = resource_path("icons")



# <a href="https://www.flaticon.com/free-icons/filter" title="filter icons">Filter icons created by Freepik - Flaticon</a>
clear_filter = f"{icon_dir}\\filter.png"

#<a href="https://www.flaticon.com/free-icons/letter-a" title="letter a icons">Letter a icons created by Ivan Repin - Flaticon</a>
active_collection = f'{icon_dir}\\letter-a.png'

window_icon = f'{icon_dir}\\window_icon.png'
step_incomplete = f'{icon_dir}\\checkbox.png'
step_complete = f'{icon_dir}\\accept.png'
caution = f'{icon_dir}\\caution.png'
configure = f'{icon_dir}\\settings.png'
open_folder = f'{icon_dir}\\open-folder.png'
connected_true = f'{icon_dir}\\checked.png'
connected_false = f'{icon_dir}\\cancel.png'
refresh = f'{icon_dir}\\refresh.png'
import_icon = f'{icon_dir}\\import.png'
export_icon = f'{icon_dir}\\export.png'
upload_icon = f'{icon_dir}\\upload.png'
database_good = f'{icon_dir}\\database_good.png'
database_bad = f'{icon_dir}\\database_bad.png'
profile = f'{icon_dir}\\login.png'
help_icon = f'{icon_dir}\\help.png'
exit_icon = f'{icon_dir}\\exit.png'