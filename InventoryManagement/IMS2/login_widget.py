import sys
import bcrypt
from PySide6.QtWidgets import (
    QWidget, QDialog, QLabel, QPushButton, QLineEdit,
    QMessageBox, QFormLayout, QVBoxLayout, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlRelation
from db_utils import DbConfig


class InputGUI(QWidget):
    def __init__(self, config_file, parent=None):
        super().__init__()
        self.parent = parent
        self.db_config_file = config_file
        self.initializeUI()

    def initializeUI(self):
        """Initialize the Login GUI window."""
        self.createConnection()
        self.setFixedSize(300, 200)
        self.setWindowTitle("로그인")
        self.setupWindow()

    def createConnection(self):
        """Set up the connection to the database.
        Check for the tables needed."""
        config_options = DbConfig(self.db_config_file)
        host = config_options.host
        port = int(config_options.port)
        user = config_options.user
        db_name = config_options.database
        passwd = config_options.passwd

        database = QSqlDatabase.addDatabase("QPSQL")
        database.setHostName(host)
        database.setPort(port)
        database.setUserName(user)
        database.setPassword(passwd)
        database.setDatabaseName(db_name)
        if not database.open():
            print(database.lastError())
            print("Unable to Connect.")
            sys.exit(1)  # Error code 1 - signifies error
        else:
            print("Connected")

        # Check if the tables we need exist in the database
        # tables_needed = {"users"}
        # tables_not_found = tables_needed - set(database.tables())
        # if tables_not_found:
        tables = database.tables()
        if "users" not in tables:
            QMessageBox.critical(None, "Error",
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
        connect_button.clicked.connect(self.connectToDatabase)

        new_user_button = QPushButton("No Account?")
        new_user_button.clicked.connect(self.create_new_user)

        main_v_box = QVBoxLayout()
        main_v_box.setAlignment(Qt.AlignTop)
        main_v_box.addWidget(header_label)
        main_v_box.addSpacing(20)
        main_v_box.addLayout(login_form)
        main_v_box.addSpacing(20)
        main_v_box.addWidget(connect_button)
        main_v_box.addWidget(new_user_button)

        self.setLayout(main_v_box)

    def query_user_password(self, user_name):
        query = QSqlQuery()
        query.prepare("SELECT user_password FROM users WHERE user_name = ?")
        query.addBindValue(user_name)
        query.exec()

        result = None
        if query.next():
            result = query.value(0)
            print("Got a password!")
        else:
            print("no password")

        return result

    def insert_user_info(self, user_name, user_pw):
        query = QSqlQuery()
        print(f'inserting {user_name}, {user_pw}')
        query.prepare("INSERT INTO users (user_name, user_password) VALUES (?, ?)")
        query.addBindValue(user_name)
        query.addBindValue(user_pw)

        if query.exec():
            print("Inserted!")
        else:
            print(f"{query.lastError()}")


    def encrypt_password(self, password):
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8', salt))
        return hashed_password

    def verify_password(self, input_password, stored_password):
        return input_password == stored_password
        # Hash the input password with the same salt used to hash the stored password
        hashed_input_password = bcrypt.hashpw(input_password.encode('utf-8'),
                                              stored_password.encode('utf-8'))

        # Compare the hashed input password with the stored password
        return hashed_input_password == stored_password

    def connectToDatabase(self):
        """
        Check the user's information. Close the login window if a match
        is found, and open the inventory manager window.

        :return:
        """
        # Collect information that the user entered
        user_name = self.user_entry.text()
        password = self.password_entry.text()

        print(user_name)
        stored_password = self.query_user_password(user_name)
        password_verified = self.verify_password(password, stored_password)
        if password_verified:
            print('verified')
        else:
            print('not verified')

        # if (user_name, password) in users.items():
        #     self.close()
        #     # Open the SQL management application
        #     time.sleep(0.5)  # Pause slightly before showing the parent window
        #     self.parent.show()
        # else:
        #     QMessageBox.warning(self, "Information Incorrect",
        #                         "The user name or password is incorrect.", QMessageBox.Close)

    def create_new_user(self):
        """Set up the dialog box for the user to create a new user account."""
        self.hide()  # Hide the login window
        self.new_user_dialog = QDialog(self)
        self.new_user_dialog.setWindowTitle("Create New User")

        header_label = QLabel("Create New User Account")
        self.new_user_entry = QLineEdit()

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.addRow("New User Login:", self.new_user_entry)
        dialog_form.addRow("New Password", self.new_password)
        dialog_form.addRow("Confirm Password", self.confirm_password)

        # Create sign up button
        create_acct_button = QPushButton("Create New Account")
        create_acct_button.clicked.connect(self.accept_user_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addWidget(header_label)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(create_acct_button)

        self.new_user_dialog.setLayout(dialog_v_box)
        self.new_user_dialog.show()

    def accept_user_info(self):
        """Verify that the user's passwords match. If so, save them user's
        info to the json file and display the login window."""
        user_name_text = self.new_user_entry.text()
        pswd_text = self.new_password.text()
        confirm_text = self.confirm_password.text()
        if pswd_text != confirm_text:
            QMessageBox.warning(self, "Error Message",
                                "The passwords you entered do not match. Please try again.",
                                QMessageBox.Close)
        else:
            # If the passwords match
            self.insert_user_info(user_name_text, pswd_text)
        self.new_user_dialog.close()
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = InputGUI('db_settings')
    login_window.show()
    sys.exit(app.exec())