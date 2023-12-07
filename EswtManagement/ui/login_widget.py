import sys
from time import sleep
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QMessageBox,
    QFormLayout, QVBoxLayout, QApplication,
)
from PySide6.QtCore import Qt, QByteArray, Signal
from PySide6.QtGui import QFont
from common.auth_util import *
from db.db_utils import QtDbUtil
from common.d_logger import Logs
from ui.change_pw_diaglog import ChgPwDialog
from ui.register_new_user_dialog import NewUserDialog


logger = Logs().get_logger("main")


class LoginWidget(QWidget):
    start_main = Signal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.db_util = QtDbUtil()
        self.init_ui()

    def init_ui(self):
        """Initialize the Login GUI window."""
        self.setFixedSize(300, 300)
        self.setWindowTitle("로그인")

        """Set up the widgets for the login GUI."""
        header_label = QLabel("다나을 재고 관리")
        header_label.setFont(QFont('Arial', 20))
        header_label.setAlignment(Qt.AlignCenter)

        self.user_entry = QLineEdit()
        self.user_entry.setMinimumWidth(150)

        self.password_entry = QLineEdit()
        self.password_entry.setMinimumWidth(150)
        self.password_entry.setEchoMode(QLineEdit.Password)

        # Arrange the QLineEdit widgets into a QFormLayout
        login_form = QFormLayout()
        login_form.setLabelAlignment(Qt.AlignLeft)
        login_form.addRow("Login Id:", self.user_entry)
        login_form.addRow("Password:", self.password_entry)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.process_login)
        # respond to returnPressed
        connect_button.setAutoDefault(True)

        change_password_button = QPushButton("Change password")
        change_password_button.clicked.connect(lambda: self.process_login(change_pw=True))
        change_password_button.setAutoDefault(True)

        new_user_button = QPushButton("Sign up")
        new_user_button.clicked.connect(self.register_new_user)
        new_user_button.setAutoDefault(True)

        main_v_box = QVBoxLayout()
        main_v_box.setAlignment(Qt.AlignTop)
        main_v_box.addWidget(header_label)
        main_v_box.addSpacing(20)
        main_v_box.addLayout(login_form)
        main_v_box.addSpacing(20)
        main_v_box.addWidget(connect_button)
        main_v_box.addWidget(change_password_button)
        main_v_box.addSpacing(10)
        main_v_box.addWidget(connect_button)
        main_v_box.addWidget(new_user_button)

        self.setLayout(main_v_box)

    def verify_user(self, password, user_name):
        # The following code converts QByteArray to PyBtye(bytes) format
        # stored_pwd: type is QByteArray hex format
        query_stmt = f"SELECT * FROM users WHERE user_name = '{user_name}'"
        db_record = self.db_util.query_info(query_stmt)
        stored_pw: QByteArray = db_record.get('user_password', None)
        if stored_pw is None:
            return False

        # convert QByteArray to bytes
        stored_pw_bytes: bytes = stored_pw.data()
        password_verified = verify_password(password, stored_pw_bytes)

        return password_verified

    def process_login(self, change_pw=False):
        """
        Check the user's information. Close the login window if a match
        is found, and open the inventory manager window.

        :return:
        """
        # Collect information that the user entered
        user_name = self.user_entry.text()
        password = self.password_entry.text()

        password_verified = self.verify_user(password, user_name)
        if password_verified:
            if change_pw:
                self.change_passwd(user_name)
            else:
                # Close login and open the SQL management application
                self.close()
                sleep(0.5)  # Pause slightly before showing the parent window
                self.start_main.emit(user_name)
                logger.debug("Passed!!!")
        else:
            QMessageBox.warning(self,
                                "Information Incorrect",
                                "The user name or password is incorrect.",
                                QMessageBox.Close)

    def change_passwd(self, user_name):
        self.chang_pw_dialog = ChgPwDialog(self.db_util)
        self.chang_pw_dialog.change_passwd(user_name)

    def register_new_user(self):
        self.reg_new_user_dialog = NewUserDialog(self.db_util)
        self.reg_new_user_dialog.register_new_user()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWidget()
    login_window.show()
    sys.exit(app.exec())