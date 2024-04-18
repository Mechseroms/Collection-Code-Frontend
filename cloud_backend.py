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
        self.server_address_label = QLabel()
        self.server_address_label.setText("Address")
        
        
        self.server_port = QLineEdit()
        self.server_port_label = QLabel()
        self.server_port_label.setText("Port")

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
        
        self.grid_layout.addWidget(self.server_port_label, 1, 0)
        self.grid_layout.addWidget(self.server_port, 1, 1)

        self.grid_layout.addWidget(self.username_label, 2, 0)
        self.grid_layout.addWidget(self.username, 2,1)

        self.grid_layout.addWidget(self.password_label, 3, 0)
        self.grid_layout.addWidget(self.password, 3, 1)

        self.grid_layout.addWidget(self.connect_button, 4, 1)


        self.setLayout(self.grid_layout)


        self.setFixedSize(300, 200)
        self.user_data = {}
        self.show()
    
    def __login(self):
        user_data = login(self.username.text(), self.password.text())
        print(user_data)
        if user_data != False:
            self.user_data = user_data    
        self.accept()


def ping():
    url = "http://127.0.0.1:5000/check_server"
    request = requests.get(url)
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
        r = requests.post(f"http://127.0.0.1:5000/upload_app", files=files)
        print(r)
        return True
    return False

def login(username, password):
    url = "http://127.0.0.1:5000/login_app"
    headers = {'Content-Type': 'application/json'}
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, headers=headers, json=data)
    user_data = {}
    if response.status_code == 200:
        user_data = response.json()
        app_settings.username = username
        app_settings.password = password
        
        url = "http://127.0.0.1:5000/login_app/avatar"
        response = requests.post(url, json=data)
        if response.status_code == 200:
            im = Image.open(BytesIO(response.content))
            im.save(f"icons/avatars/{data['username']}_avatar.png")
            user_data['avatar'] = f"icons/avatars/{data['username']}_avatar.png"
            return user_data
        user_data['avatar'] = f"icons/avatars/default_avatar.png"
        return user_data
    return False
            