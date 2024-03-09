import sys
import main_window, handlers.koreainvest, secret.keys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        layout.addWidget(self.api_key_label)
        layout.addWidget(self.api_key_input)

        self.api_secret_label = QLabel("API Secret:")
        self.api_secret_input = QLineEdit()
        layout.addWidget(self.api_secret_label)
        layout.addWidget(self.api_secret_input)

        self.hts_id_label = QLabel("HTS ID:")
        self.hts_id_input = QLineEdit()
        layout.addWidget(self.hts_id_label)
        layout.addWidget(self.hts_id_input)

        self.account_no_label = QLabel("Account:")
        self.account_no_input = QLineEdit()
        layout.addWidget(self.account_no_label)
        layout.addWidget(self.account_no_input)

        self.account_password_label = QLabel("Password:")
        self.account_password_input = QLineEdit()
        layout.addWidget(self.account_password_label)
        layout.addWidget(self.account_password_input)

        self.mock_trading_checkbox = QCheckBox('Mock Trading')
        layout.addWidget(self.mock_trading_checkbox)
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.central_widget.setLayout(layout)

    def login(self):
        api_key = self.api_key_input.text()
        api_secret = self.api_secret_input.text()
        hts_id = self.hts_id_input.text()
        account_no = self.account_no_input.text()
        account_password = self.account_password_input.text()
        mock_trading = self.mock_trading_checkbox.isChecked()
        
        if api_key and api_secret and hts_id and account_no and account_password:
            self.close()
            try:
                b = handlers.koreainvest.create_broker(api_key, api_secret, account_no, "서울", mock_trading)
            except:
                QMessageBox.warning(self, "Login Failed", "Failed to Login")
                return
            self.open_main_window(api_key, api_secret, hts_id, account_no, account_password, mock_trading)
        else:
            QMessageBox.warning(self, "Login Failed", "Please fill in all fields.")
            
    def open_main_window(self, key, secret, id, account, pwd, mock):
        self.main_window = main_window.MyApp({
            "apikey": key,
            "apisecret": secret,
            "htsid": id,
            "accno" : account,
            "accpwd" : pwd,
            "mock": mock
        })
        self.main_window.show()
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(open('./resources/style.qss', 'r').read())
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()