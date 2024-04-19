from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QLabel
import requests, json
from PIL import Image
from io import BytesIO
import settings


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
        self.accept()


def ping():
    request = requests.get(f"{settings.app_settings.connected_server}/ping")
    if request.status_code == 200:
        return True
    return False

def upload_file(filename, file_path, external_data: dict):
    if ping():
        external_data['username'] = settings.app_settings.username
        external_data['password'] = settings.app_settings.password
        external_data['filename'] = filename
        files = [
            ('file', ('file', open(file_path, 'rb'), 'application/octet')),
            ('datas', ('datas', json.dumps(external_data), 'application/json')),
        ]
        r = requests.post(f"{settings.app_settings.connected_server}/upload_app", files=files)
        return True
    return False

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
        
        url = f"{settings.app_settings.connected_server}/login_app/avatar"
        response = requests.post(url, json=data)
        if response.status_code == 200:
            im = Image.open(BytesIO(response.content))
            im.save(f"./icons/avatars/{data['username']}_avatar.png")
            user_data['avatar'] = f"icons/avatars/{data['username']}_avatar.png"
            return user_data
        user_data['avatar'] = f"icons/avatars/default_avatar.png"
        return user_data
    return False
            