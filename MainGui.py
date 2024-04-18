from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QWidget, QToolBar, QAction,
                             QSizePolicy, QToolButton, QTreeWidget, 
                             QListWidget, QListWidgetItem, QTreeWidgetItem, QGroupBox, QLineEdit, 
                             QLabel, QTextEdit, QPushButton, QFileDialog, QSlider, QHBoxLayout, QVBoxLayout, QFrame, QGridLayout, QComboBox, QFontDialog, QTextBrowser)
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon, QFont
from qtwidgets import Toggle
from striprtf.striprtf import rtf_to_text
from cloud_backend import LoginDialog, login, upload_file
import tempfile
import export_process, import_process, upload_process
import settings, pathlib, os, sys, icons, easySQL, tables, json, zipfile

global status_bar
global tool_bar

class ModificationItem(QTreeWidgetItem):
    def __init__(self):
        super().__init__()
        self.id = 0

class ColectionItem(QListWidgetItem):
    def __init__(self):
        super().__init__()
        self.id = 0

class MainGui(QMainWindow):
    def __init__(self) -> None:
        self.app_settings = settings.app_settings
        super().__init__()
        self.setWindowTitle(self.app_settings.get_setting('window_title'))
        self.setMaximumHeight(720)
        self.setMaximumWidth(1280)
        self.resize(self.app_settings.get_setting('window_width'), self.app_settings.get_setting('window_height'))
        self.setWindowIcon(QIcon(icons.window_icon))

        self.widget = QWidget()

        self.tool_bar = QToolBar()
        self.addToolBar(self.tool_bar)
        self.tool_bar.setMovable(False)
        self.tool_bar.setFixedHeight(35)

        self.exit_app = QAction("Save and exit", self)
        self.exit_app.setIcon(QIcon(icons.exit_icon))
        self.exit_app.triggered.connect(self.exit_application)
        self.tool_bar.addAction(self.exit_app)

        self.tool_bar.addSeparator()

        # need an import button that imports a selected pcmp from a file dialog
        self.import_tool = QAction("Import PCMP File", self)
        self.import_tool.setToolTip("Imports a PCMP file from system into your Penumbra installation.")
        self.import_tool.setIcon(QIcon(icons.import_icon))
        self.import_tool.triggered.connect(self.import_collection)        
        self.tool_bar.addAction(self.import_tool)
        
        # need an export button that exports a selected collection in the list
        self.export_tool = QAction("Export Collection to Archive", self)
        self.export_tool.setToolTip("Export collection from Penumbra installation into a share-able PCMP archive")
        self.export_tool.setIcon(QIcon(icons.export_icon))
        self.export_tool.setEnabled(False)
        self.export_tool.triggered.connect(self.export_collection)
        self.tool_bar.addAction(self.export_tool)
        
        # need an upload dummy button for future features
        self.upload_tool = QAction("Upload Collection to the set up server.", self)
        self.upload_tool.setToolTip("If a server has been configured alongside a profile on that server, you may upload the collection straight there for others to download without needing to share it.")
        self.upload_tool.setIcon(QIcon(icons.upload_icon))
        self.upload_tool.setEnabled(False)
        self.upload_tool.triggered.connect(self.upload_collection)
        self.tool_bar.addAction(self.upload_tool)

        self.refresh_tool = QAction("Refresh", self)
        self.refresh_tool.setToolTip("Refreshes the loaded data and selected collection data!")
        self.refresh_tool.setIcon(QIcon(icons.refresh))
        self.refresh_tool.setEnabled(True)
        self.tool_bar.addAction(self.refresh_tool)

        #add a spacer
        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tool_bar.addWidget(self.spacer)
        
        self.mode_label  = QLabel()
        self.mode_label.setText('Mode')
        self.tool_bar.addWidget(self.mode_label)

        self.mode_slider  = Toggle()
        self.mode_slider.setToolTip('Sets the mode between basic or advanced details allowing for more manipulation of imports and exports. Only use this if you know what you are doing!')
        self.mode_slider.toggled.connect(self.mode_change)
        self.tool_bar.addWidget(self.mode_slider)


        self.settings_button = QAction("Settings", self)
        self.settings_button.setIcon(QIcon(icons.configure))
        self.tool_bar.addAction(self.settings_button)
        self.settings_button.triggered.connect(self.change_font_size)

        self.help_button = QAction("Help", self)
        self.help_button.setIcon(QIcon(icons.help_icon))
        self.tool_bar.addAction(self.help_button)

        # need a database connection indicator
        self.database_indicator = QAction("Database Status", self)
        self.database_indicator.setIcon(QIcon(icons.database_bad))
        self.tool_bar.addAction(self.database_indicator)
        # need a sign-in/profile placard that acts as a button to change login info
        self.profile_indicator = QToolButton()
        self.profile_indicator.setText("Profile/Login")
        self.profile_indicator.setToolTip("If a server is configured use this to attempt so sign in to a profile on that server. This profile will be used for when uploading a collection.")
        self.profile_indicator.setIcon(QIcon(icons.profile))
        self.profile_indicator.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.profile_indicator.clicked.connect(self.login_user)
        self.tool_bar.addWidget(self.profile_indicator)

        # main vertical layout object
        self.horizontal_layout = QHBoxLayout(self)

        # collection layout V
        self.collection_vertical_layout = QVBoxLayout()
        # self.inner_canvas.setStyleSheet("background-color: blue")
        
        self.collection_list = QListWidget()
        self.col_frame = QFrame()
        self.col_frame.setFrameStyle(QFrame.Panel)
        
        self.collection_list.setFixedWidth(200)
        self.collection_list.setFixedHeight(300)
        
        self.collection_vertical_layout.addWidget(self.collection_list)
        self.collection_vertical_layout.addWidget(self.col_frame)

        # Close out collection Layout V

        
        self.details_vertical_layout = QVBoxLayout()
        
        self.details_group = QGroupBox()
        self.details_group.setTitle('Collection Details')

        self.details_horizontal_layout = QHBoxLayout()

        self.horizontal_form_layout = QGridLayout()
        # ---- Form Control Start ---->
        self.name_label = QLabel()
        self.name_label.setText("Collection Name")
        self.name_edit = QLineEdit()
        self.name_edit.setMaximumWidth(200)

        self.version_label = QLabel()
        self.version_label.setText("Version")
        self.version_edit = QLineEdit()
        self.version_edit.setMaximumWidth(200)

        self.comment_label = QLabel()
        self.comment_label.setText("Comments")
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(150)
        self.comment_edit.setMaximumHeight(250)


        self.horizontal_form_layout.addWidget(self.name_label, 0, 0)
        self.horizontal_form_layout.addWidget(self.name_edit, 0, 1)

        self.horizontal_form_layout.addWidget(self.version_label, 1, 0)
        self.horizontal_form_layout.addWidget(self.version_edit, 1, 1)
        
        self.horizontal_form_layout.addWidget(self.comment_label, 2, 0)
        self.horizontal_form_layout.addWidget(self.comment_edit, 2, 1)

        # ---- Form Control End ---->

        self.details_group.setLayout(self.horizontal_form_layout)
        self.details_group.setFixedHeight(300)
        self.details_group.setMaximumWidth(500)
        

        self.character_links = QGroupBox()
        self.character_links.setTitle("Character Links")
        self.character_links.setFixedHeight(300)
        self.character_links.setFixedWidth(200)

        self.character_grid_layout = QGridLayout()
        self.links_list = QListWidget()
        self.character_grid_layout.addWidget(self.links_list)

        self.character_links.setLayout(self.character_grid_layout)

        self.search_horizontal_layout = QHBoxLayout()
        
        self.clear_filter_mods = QPushButton()
        self.clear_filter_mods.setIcon(QIcon(icons.clear_filter))
        self.clear_filter_mods.setMaximumWidth(30)
        self.clear_filter_mods.setMaximumHeight(30)
        
        self.mod_list_search = QLineEdit()
        self.mod_list_search.textEdited.connect(self.filter_mods)        
        self.mod_list_search.setFixedHeight(30)
        self.mod_list_search.setFixedWidth(200)

        self.search_horizontal_layout.addWidget(self.clear_filter_mods)
        self.search_horizontal_layout.addWidget(self.mod_list_search)

        self.search_horizontal_layout.setSpacing(5)
        self.search_horizontal_layout.setAlignment(Qt.AlignLeft)

        
        self.mod_list = QTreeWidget()


        self.details_horizontal_layout.addWidget(self.details_group)
        self.details_horizontal_layout.addWidget(self.character_links)
        
        self.details_vertical_layout.addLayout(self.details_horizontal_layout)
        self.details_vertical_layout.addLayout(self.search_horizontal_layout)
        self.details_vertical_layout.addWidget(self.mod_list)
        # ---- Details/Modlist Layout V ---- >

        self.advanced_widget_canvas = QWidget()
        self.advanced_widget_canvas.setLayout(self.details_vertical_layout)

        self.horizontal_layout.addLayout(self.collection_vertical_layout)
                

        self.basic_vertical_layout = QVBoxLayout()
        self.basic_horizontal_layout = QHBoxLayout()

        self.basic_vertical_layout.addLayout(self.basic_horizontal_layout)

        self.basic_group = QGroupBox()
        self.basic_group.setTitle("Basic Mode Instructions")
        self.basic_horizontal_layout.addWidget(self.basic_group)

        self.group_layout = QGridLayout()
        self.basic_group.setLayout(self.group_layout)
        
        
        text = str()
        with open("inst_text.rtf", "r+") as _file:
            text = _file.read()

        text = rtf_to_text(text)

        self.label1 = QLabel()
        #self.label1.setAcceptRichText(True)
        self.label1.setText(text)
        self.label1.setWordWrap(True)
        self.label1.setMinimumWidth(400)
        

        self.group_layout.addWidget(self.label1, 0, 0)
        self.group_layout.setAlignment(Qt.AlignLeft)
        self.group_layout.addWidget(self.name_edit, 1, 0)
        

        self.basic_widget_canvas = QWidget()
        self.basic_widget_canvas.setLayout(self.basic_vertical_layout)
    
        # this is where the if split needs to happen
    
        basic_mode = True
        advanced_mode = False
        self.horizontal_layout.addWidget(self.advanced_widget_canvas)
        self.horizontal_layout.addWidget(self.basic_widget_canvas)


        if advanced_mode:
            self.basic_widget_canvas.setHidden(True)
            self.advanced_widget_canvas.setHidden(False)
        if basic_mode:
            self.basic_widget_canvas.setHidden(False)
            self.advanced_widget_canvas.setHidden(True)


        self.widget.setLayout(self.horizontal_layout)
        self.setCentralWidget(self.widget)

        self.selected_item = None
        self.selected_item_meta = {}
        self.selected_item_id = 0
        self.selected_item_data = {}

    def change_font_size(self, a):
        (font, ok) = QFontDialog.getFont(QFont("Helvetica [Cronyx]", 10), self)
        if ok:
            # the user clicked OK and font is set to the font the user selected
            self.setFont(font)

    def __post__init__(self):
        self.collection_list.itemClicked.connect(self.populate_details)
        self.repopulate_collections()
        self.repopulate_modslist()

    def exit_application(self):
        self.app_settings.save_settings()
        sys.exit()

    def mode_change(self, a):
        if a:
            self.setWindowTitle(f"{self.app_settings.get_setting('window_title')} (Advanced Mode)")
            self.app_settings.set_setting('advanced_mode', True)
            self.basic_widget_canvas.setHidden(True)
            self.advanced_widget_canvas.setHidden(False)
        else:
            self.setWindowTitle(f"{self.app_settings.get_setting('window_title')} (Basic Mode)")
            self.app_settings.set_setting('advanced_mode', False)
            self.advanced_widget_canvas.setHidden(True)
            self.basic_widget_canvas.setHidden(False)


        if not self.app_settings.get_setting('advanced_mode'):
            self.version_edit.setDisabled(True)
            self.comment_edit.setDisabled(True)
            self.links_list.setDisabled(True)
            self.mod_list_search.setDisabled(True)
            self.clear_filter_mods.setDisabled(True)
            
        else:
            self.version_edit.setDisabled(False)
            self.comment_edit.setDisabled(False)
            self.links_list.setDisabled(False)
            self.mod_list_search.setDisabled(False)
            self.clear_filter_mods.setDisabled(False)
        
        self.repopulate_modslist()

    def get_export_upload_payload(self) -> dict:
        collection_data = easySQL.fetchone_from_table(tables.collections, filter=('collection_id', self.selected_item_id))
        collection_settings = json.loads(collection_data.settings)
        
        # The below process handles the repackaging payload for a collection allowing for advanced changes such
        # as enabling or putting a modification on ignore.
        # TODO: enabled_mods and mods_to_copy could be consolidated into a single dictionary
        enabled_mods = {}
        mods_to_copy = []
        count = self.mod_list.topLevelItemCount()
        for index in range(count):
            item = self.mod_list.topLevelItem(index)
            if item.checkState(0) == 2:
                modification_row = easySQL.fetchone_from_table(tables.modifications, filter=('name', item.text(0)))
                mods_to_copy.append((modification_row.name, modification_row.mod_path, modification_row.total_files))
                try:
                    mod_settings = collection_settings[item.text(0)]
                    mod_settings['Enabled'] = True
                    enabled_mods[item.text(0)] = mod_settings
                except:
                    pass

        payload: {str, any} = {
            'collection_json':{
                'Version': collection_data.version,
                'Name': self.name_edit.text(),
                'Settings': enabled_mods,
                'Inheritance': []
            },
            'character_links': json.loads(collection_data.character_links),
            'meta_data': {
                "collection_name": self.name_edit.text(),
                "version": self.version_edit.text(),
                "comments": self.comment_edit.toPlainText()
            },
            'mods_to_copy': mods_to_copy
        }

        return payload
    
    def upload_collection(self):
        payload = self.get_export_upload_payload()
 
        progress_dialog = upload_process.UploadProgressDialog(self, payload)
        progress_dialog.start_upload()
    
    def export_collection(self):
    
        payload = self.get_export_upload_payload()
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_():
              save_directory = dialog.selectedFiles()[0]
              payload['save_directory'] = save_directory
              
              # todo: remove this
              with open('test.json', 'w+') as file:
                  json.dump(payload, file, indent=2)

              progress_dialog = export_process.ExportProgressDialog(self, payload)
              progress_dialog.start_exportation()
    
    def import_collection(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter("Archive (*.pcmp)")
        if dialog.exec_():
            path_to_zip = pathlib.Path(dialog.selectedFiles()[0])
            print(path_to_zip) # do some validation on the path
            


            with zipfile.ZipFile(path_to_zip) as collection_pcmp:
                
                
                collection_name = ''
                
                with collection_pcmp.open("meta.json") as _file:
                    meta = json.load(_file)
                    collection_name = meta["collection_name"]

                with collection_pcmp.open(f"{collection_name}.json") as _file:
                    collection_data = json.load(_file)

            if collection_name in [row.name for row in easySQL.fetchall_from_table(tables.collections)]:
                warning_dialog = QMessageBox(self)
                warning_dialog.setWindowTitle('Collection already exists...')
                warning_dialog.setText(f"It appears that this collection already exists, would you like to overwrite it?")
                warning_dialog.setIcon(QMessageBox.Question)
                warning_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                button = warning_dialog.exec()

                if button == QMessageBox.No:
                    return


            payload = {
                'collection_json': collection_data,
                'meta_data': meta,
                'path_to_zip': path_to_zip,
                'mods_to_copy': [key for key in collection_data['Settings'].keys()]
            }


            print(payload)
            self.progress_dialog = import_process.ImportProgressDialog(self, payload)
            self.progress_dialog.import_collection()

    def login_user(self):
        
        dialog = LoginDialog(self)
        if dialog.exec_():
            self.app_settings.user_data = dialog.user_data
            self.app_settings.connected = True
            self.profile_indicator.setIcon(QIcon(settings.app_settings.user_data['avatar']))
            self.profile_indicator.setText(settings.app_settings.username)
            self.database_indicator.setIcon(QIcon(icons.database_good))
    
    def filter_mods(self):
        filter = self.mod_list_search.text()
        count = self.mod_list.topLevelItemCount()
        for index in range(count):
            item = self.mod_list.topLevelItem(index)
            present_filter = [mod_name.strip() for mod_name in json.loads(self.selected_item_data.settings).keys()]
            if filter in item.text(0) and item.text(0) in present_filter:
                item.setHidden(False)
            else:
                item.setHidden(True)
            
    def repopulate_modslist(self, enabled: list = [], present: list = []):
        self.mod_list.clear()
        self.mod_list.setHeaderLabel('Modification Name')
        self.mod_list.setAlternatingRowColors(True)

        list = easySQL.fetchall_from_table(tables.modifications) 
        for d, row in enumerate(list):
            
            
            
            item = ModificationItem()
            item.setText(0, row.name)

            if row.name in enabled:
                item.setCheckState(0, 2)
            else:
                item.setCheckState(0, 0)

            item.id = row.mod_id
            self.mod_list.addTopLevelItem(item)
            
            if row.name in present or len(present)==0:
                item.setHidden(False)
                item.setDisabled(False)
            else:
                item.setHidden(True)
                item.setDisabled(True)

            if not self.app_settings.get_setting('advanced_mode'):
                item.setDisabled(True)

    def repopulate_collections(self):
        self.collection_list.clear()
        self.collection_list.setAlternatingRowColors(True)

        list = [(row.collection_id, row.name) for row in easySQL.fetchall_from_table(tables.collections)]
        for id, name in list:
            item = ColectionItem()
            item.setText(name)
            item.id = id
            item.setToolTip(f"{id}")
            self.collection_list.addItem(item)

    def repopulate_character_links(self):
        self.links_list.clear()
        links = json.loads(self.selected_item_data.character_links)

        if links['Default']:
            item = QListWidgetItem()
            item.setText("Default")
            item.setCheckState(2)
            self.links_list.addItem(item)
        if links["Yourself"]:
            item = QListWidgetItem()
            item.setText("Yourself")
            item.setCheckState(2)
            self.links_list.addItem(item)
        if len(links["Individuals"]) > 0:
            for link in links["Individuals"]:
                item = QListWidgetItem()
                item.setText(link["Display"])
                item.setCheckState(2)
                self.links_list.addItem(item)

    def populate_details(self, item):
        
        self.export_tool.setEnabled(True)
        if self.app_settings.connected: 
            self.upload_tool.setEnabled(True)
        else:
            self.upload_tool.setEnabled(False)
        self.selected_item_id = item.id
        self.selected_item = item
        self.selected_item_data = easySQL.fetchone_from_table(tables.collections, filter=("collection_id", item.id))
        self.selected_item_meta = easySQL.fetchone_from_table(tables.metadata, filter=("collection_name", self.selected_item_data.name))
        settings_filter = [mod_name.strip() for mod_name, settings in json.loads(self.selected_item_data.settings).items() if settings['Enabled']]
        present_filter = [mod_name.strip() for mod_name in json.loads(self.selected_item_data.settings).keys()]
        self.repopulate_modslist(enabled=settings_filter, present=present_filter)
        self.repopulate_character_links()
        self.name_edit.setText(self.selected_item_data.name)
        self.version_edit.setText(self.selected_item_meta.version)
        self.comment_edit.setPlainText(self.selected_item_meta.comments)

        if not self.app_settings.get_setting('advanced_mode'):
            self.version_edit.setDisabled(True)
            self.comment_edit.setDisabled(True)
            self.links_list.setDisabled(True)
            self.mod_list_search.setDisabled(True)
            self.clear_filter_mods.setDisabled(True)
            self.mod_list.setDisabled(True)
        else:
            self.version_edit.setDisabled(False)
            self.comment_edit.setDisabled(False)
            self.links_list.setDisabled(False)
            self.mod_list_search.setDisabled(False)
            self.clear_filter_mods.setDisabled(False)
            self.mod_list.setDisabled(False)