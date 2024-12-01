from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QLabel, QVBoxLayout, QRadioButton
import requests, json
from PIL import Image
from io import BytesIO
import settings
import pathlib, os


global app_settings 
app_settings = settings.app_settings

class LoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Login')
        self.grid_layout = QGridLayout()

        self.server_address = QLineEdit()
        self.server_address.setText(settings.app_settings.connected_server)
        self.server_address_label = QLabel()
        self.server_address_label.setText("Server")

        self.username = QLineEdit()
        self.username.setText(app_settings.username)
        self.username_label = QLabel()
        self.username_label.setText("Username")

        self.password = QLineEdit()
        self.password.setText(app_settings.password)
        self.password_label = QLabel()
        self.password_label.setText("Password")

        self.connect_button = QPushButton()
        self.connect_button.setText("Connect")
        self.connect_button.clicked.connect(self.__login)

        self.grid_layout.addWidget(self.server_address_label, 0, 0)
        self.grid_layout.addWidget(self.server_address, 0, 1)
        
        self.grid_layout.addWidget(self.username_label, 1, 0)
        self.grid_layout.addWidget(self.username, 1,1)

        self.grid_layout.addWidget(self.password_label, 2, 0)
        self.grid_layout.addWidget(self.password, 2, 1)

        self.grid_layout.addWidget(self.connect_button, 3, 1)


        self.setLayout(self.grid_layout)


        self.setFixedSize(300, 200)
        self.user_data = {}
        self.show()
    
    def __login(self):
        settings.app_settings.username = self.username.text()
        settings.app_settings.password = self.password.text()
        settings.app_settings.connected_server = self.server_address.text()
        user_data = login(settings.app_settings.username, settings.app_settings.password)
        if user_data != False:
            self.user_data = user_data

        with open('log.txt', 'w+') as file:
            file.write(json.dumps(user_data))  
        self.accept()

def ping(url):
    request = requests.get(url)
    if request.status_code == 200:
        return True
    return False


def upload_file(filename, file_path, external_data: dict):  
    external_data['username'] = settings.app_settings.username
    external_data['password'] = settings.app_settings.password
    external_data['filename'] = filename
    files = [
        ('file', ('file', open(file_path, 'rb'), 'application/octet')),
        ('datas', ('datas', json.dumps(external_data), 'application/json')),
    ]
    r = requests.post(f"{settings.app_settings.connected_server}/upload_app", files=files)

def login(username, password):
    headers = {'Content-Type': 'application/json'}
    data = {
        "username": username,
        "password": password
    }

    response = requests.post(f"{settings.app_settings.connected_server}/login_app", headers=headers, json=data)
    user_data = {}
    if response.status_code == 200:
        user_data = response.json()
        settings.app_settings.username = username
        settings.app_settings.password = password
        
        response = requests.post(f"{settings.app_settings.connected_server}/login_app/avatar", json=data)
        if response.status_code == 200:
            im = Image.open(BytesIO(response.content))
            path = settings.app_settings.external_path / "avatars" / f"{data['username']}_avatar.png"
            print(path)
            im.save(path)
            user_data['avatar'] = str(path.absolute())
            return user_data
        user_data['avatar'] = f"icons/avatars/default_avatar.png"
        return user_data
    return False


class UpdateOptInDialog(QDialog):
    def __init__(self, parent, default_pipeline):
        super().__init__(parent)
        self.default_pipeline = default_pipeline
        self.setWindowTitle(f"Connectivity Opt In")
        self.setMaximumWidth(300)
        self.resize(300, 100)

        self.vertical_layout = QVBoxLayout()


        text = """This seems to be your first time loading this app and we have a important question to ask. That is; do you wish to opt into receiving update requests from our pipelines? If you choose not to then you will not be able to connect to any servers. This is in order to ensure that you stay upto date for those servers."""
        self.message_label = QLabel()
        self.message_label.setText(text)
        self.message_label.setWordWrap(True)
        self.message_label.setFixedSize(400, 100)


        self.opt_in = QRadioButton()
        self.opt_in.setText("I Want to Opt In to Updates")
        self.opt_in.toggled.connect(self.radio_changed)

        self.pipeline_edit = QLineEdit()
        self.pipeline_edit.setEnabled(False)

        self.confirm_button = QPushButton()
        self.confirm_button.setText("Confirm")
        self.confirm_button.setMaximumWidth(60)
        self.confirm_button.setMaximumHeight(30)
        self.confirm_button.clicked.connect(self.confirm_selection)


        self.vertical_layout.addWidget(self.message_label)
        self.vertical_layout.addWidget(self.opt_in)
        self.vertical_layout.addWidget(self.pipeline_edit)
        self.vertical_layout.addWidget(self.confirm_button)

        self.setLayout(self.vertical_layout)

        self.show()
    
    def radio_changed(self, state):
        if state:
            self.pipeline_edit.setEnabled(True)
            self.pipeline_edit.setText(self.default_pipeline)
        if not state:
            self.pipeline_edit.setEnabled(False)
            self.pipeline_edit.setText("")

    def get_opt_in_state(self):
        return self.opt_in.isChecked()

    def get_pipeline(self):
        return self.pipeline_edit.text()
        
    def confirm_selection(self):
        self.accept()