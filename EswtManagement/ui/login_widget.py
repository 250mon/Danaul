import sys
from time import sleep
from typing import Dict
import bcrypt
from PySide6.QtWidgets import (
    QWidget, QDialog, QLabel, QPushButton, QLineEdit,
    QMessageBox, QFormLayout, QVBoxLayout, QApplication,
    QHBoxLayout, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt, QByteArray, Signal
from PySide6.QtGui import QFont
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from db.db_utils import ConfigReader
from common.d_logger import Logs, logging


logger = Logs().get_logger("main")


class LoginWidget(QWidget):
    start_main = Signal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.initializeUI()

    def initializeUI(self):
        """Initialize the Login GUI window."""
        self.createConnection()
        self.setFixedSize(300, 300)
        self.setWindowTitle("로그인")
        self.setupWindow()

    def createConnection(self):
        """Set up the connection to the database.
        Check for the tables needed."""
        config = ConfigReader()
        database = QSqlDatabase.addDatabase("QPSQL")
        database.setHostName(config.get_options("Host"))
        database.setPort(int(config.get_options("Port")))
        database.setUserName(config.get_options("User"))
        database.setPassword(config.get_options("Password"))
        database.setDatabaseName(config.get_options("Database"))
        if not database.open():
            logger.error("Unable to Connect.")
            logger.error(database.lastError())
            sys.exit(1)  # Error code 1 - signifies error
        else:
            logger.debug("Connected")

        # Check if the tables we need exist in the database
        # tables_needed = {"users"}
        # tables_not_found = tables_needed - set(database.tables())
        # if tables_not_found:
        tables = database.tables()
        if "users" not in tables:
            QMessageBox.critical(None,
                                 "Error",
                                 f"""<p>The following tables are missing
                                  from the database: {tables}</p>""")
            sys.exit(1)  # Error code 1 - signifies error

    def setupWindow(self):
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
        new_user_button.clicked.connect(self.register_password_dialog)
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

    def query_user_info(self, user_name) -> Dict:
        """
        query user info with user_name
        """
        query = QSqlQuery()
        query.prepare("SELECT * FROM users WHERE user_name = ?")
        query.addBindValue(user_name)
        query.exec()

        db_record = {}
        if query.next():
            db_record['user_name'] = query.value('user_name')
            db_record['user_password'] = query.value('user_password')
            db_record['user_realname'] = query.value('user_realname')
            db_record['user_job'] = query.value('user_job')
            logger.debug("Got a record!")
        else:
            logger.debug("No record found")
        return db_record

    def insert_user_info(self, db_record):
        """
        Insert db_record into DB
        """
        query = QSqlQuery()
        user_name = db_record['user_name']
        pw = QByteArray(db_record['hashed_pw'])
        logger.debug(f"{user_name}, password:{pw}")
        query.prepare("""INSERT INTO users (user_name, user_password) VALUES ($1, $2)
                            ON CONFLICT (user_name)
                            DO
                                UPDATE SET user_name = $1, user_password = $2""")
        query.addBindValue(user_name)
        # postgresql only accepts hexadecimal format
        query.addBindValue(pw)

        if query.exec():
            logger.debug("User info inserted!")
        else:
            QMessageBox.warning(self,
                                "Warning",
                                "User name or password is improper!!",
                                QMessageBox.Close)
            logger.debug("User info not inserted!")
            logger.debug(f"{query.lastError()}")

    def encrypt_password(self, password):
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password

    def verify_password(self, input_password, stored_password):
        # Hash the input password with the same salt used to hash the stored password
        hashed_input_password = bcrypt.hashpw(input_password.encode('utf-8'), stored_password)
        # Compare the hashed input password with the stored password
        return hashed_input_password == stored_password

    def verify_user(self, password, user_name):
        # The following code converts QByteArray to PyBtye(bytes) format
        # stored_pwd: type is QByteArray hex format
        db_record = self.query_user_info(user_name)
        stored_pw: QByteArray = db_record.get('user_password', '')
        if stored_pw is None:
            return False

        # convert QByteArray to bytes
        stored_pw_bytes: bytes = stored_pw.data()
        password_verified = self.verify_password(password, stored_pw_bytes)
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
            self.close()
            if change_pw:
                self.change_passwd(user_name)
            else:
                # Open the SQL management application
                sleep(0.5)  # Pause slightly before showing the parent window
                self.start_main.emit(user_name)
                logger.debug("Passed!!!")
        else:
            QMessageBox.warning(self,
                                "Information Incorrect",
                                "The user name or password is incorrect.",
                                QMessageBox.Close)

    def change_passwd(self, user_name):
        """ Change password """
        self.hide()  # Hide the login window
        # change password
        self.user_input_dialog = QDialog(self)
        self.user_input_dialog.setWindowTitle("Change Password")
        header_label = QLabel("Change Password")
        self.user_name_le = QLabel(user_name)

        self.new_password_le = QLineEdit()
        self.new_password_le.setEchoMode(QLineEdit.Password)
        self.confirm_password_le = QLineEdit()
        self.confirm_password_le.setEchoMode(QLineEdit.Password)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.addRow("New Password", self.new_password_le)
        dialog_form.addRow("Confirm Password", self.confirm_password_le)

        # Create sign up button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_user_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addWidget(header_label)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.user_input_dialog.setLayout(dialog_v_box)
        self.user_input_dialog.show()

    def register_password_dialog(self):
        """ Set up the dialog box for the user to create a new user account. """
        self.hide()  # Hide the login window
        self.user_input_dialog = QDialog(self)
        # create a new user account
        self.user_input_dialog.setWindowTitle("Create New User")
        header_label = QLabel("Create New User Account")

        # user name part
        self.user_name_le = QLineEdit()
        user_name_check_btn = QPushButton("중복확인")
        user_name_check_btn.clicked.connect(self.check_duplicate_user_name)
        user_name_hbox = QHBoxLayout()
        user_name_hbox.addWidget(self.user_name_le)
        user_name_hbox.addWidget(user_name_check_btn)

        # password part
        self.new_password_le = QLineEdit()
        self.new_password_le.setEchoMode(QLineEdit.Password)
        self.confirm_password_le = QLineEdit()
        self.confirm_password_le.setEchoMode(QLineEdit.Password)
        self.password_check_btn = QPushButton("비밀번호 확인")
        self.password_check_btn.clicked.connect(self.check_password_integrity)

        # additional info
        self.real_name_le = QLineEdit()
        self.job_cb = QComboBox()
        self.job_cb.addItems(['물리치료사', '도수치료사', '간호조무사', '방사선사'])

        # initially disabled
        self.new_password_le.setEnabled(False)
        self.confirm_password_le.setEnabled(False)
        self.password_check_btn.setEnabled(False)
        self.real_name_le.setEnabled(False)
        self.job_cb.setEnabled(False)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.addRow("아이디", user_name_hbox)
        dialog_form.horizontalSpacing()
        dialog_form.addRow("비밀번호 입력", self.new_password_le)
        dialog_form.addRow("비밀번호 확인", self.confirm_password_le)
        dialog_form.addRow("", self.password_check_btn)
        dialog_form.horizontalSpacing()
        dialog_form.addRow("이 름", self.real_name_le)
        dialog_form.addRow("직 책", self.job_cb)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_user_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addWidget(header_label)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.user_input_dialog.setLayout(dialog_v_box)
        self.user_input_dialog.show()

    def check_duplicate_user_name(self):
        self.user_name_le.setEnabled(False)
        self.new_password_le.setEnabled(True)
        self.confirm_password_le.setEnabled(True)
        self.password_check_btn.setEnabled(True)

    def check_password_integrity(self):
        pw_text = self.new_password_le.text()
        confirm_text = self.confirm_password_le.text()

        if len(pw_text) < 1 or len(confirm_text) < 1:
            QMessageBox.warning(self,
                                "Error Message",
                                "비밀번호가 형식에 맞지 않습니다.",
                                QMessageBox.Close)
        elif pw_text != confirm_text:
            QMessageBox.warning(self,
                                "Error Message",
                                "비밀번호가 일치하지 않습니다.",
                                QMessageBox.Close)
        else:
            self.new_password_le.setEnabled(False)
            self.confirm_password_le.setEnabled(False)
            self.password_check_btn.setEnabled(False)
            self.real_name_le.setEnabled(True)
            self.job_cb.setEnabled(True)

    def accept_user_info(self):
        """Verify that the user's passwords match. If so, save the user's
        info to DB and display the login window."""
        user_name_text = self.user_name_le.text()
        pw_text = self.new_password_le.text()
        confirm_text = self.confirm_password_le.text()
        if pw_text != confirm_text:
            QMessageBox.warning(self,
                                "Error Message",
                                "The passwords you entered do not match. Please try again.",
                                QMessageBox.Close)
        else:
            # If the passwords match, encrypt and save it to the db
            hashed_pw = self.encrypt_password(pw_text)
            self.insert_user_info(user_name_text, hashed_pw)
            self.user_input_dialog.close()
            self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWidget()
    login_window.show()
    sys.exit(app.exec())