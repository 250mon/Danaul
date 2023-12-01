from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLabel, QLineEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QByteArray
from db.db_utils import QtDbUtil
from common.auth_util import *


class ChgPwDialog(QDialog):

    def __init__(self, db_util: QtDbUtil, parent=None):
        self.db_util = db_util
        super().__init__(parent)

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
        self.password_check_btn = QPushButton("확인")
        self.password_check_btn.clicked.connect(self.check_password_btn_clicked)
        pw_hbox2 = QHBoxLayout()
        pw_hbox2.addWidget(self.confirm_password_le)
        pw_hbox2.addWidget(self.password_check_btn)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("새로운 비밀번호", self.new_password_le)
        dialog_form.addRow("비밀번호 확인", pw_hbox2)

        # Create sign up button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_user_info)
        self.ok_button.setEnabled(False)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addWidget(header_label)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(self.ok_button)

        self.user_input_dialog.setLayout(dialog_v_box)
        self.user_input_dialog.show()

    def check_password_btn_clicked(self):
        pw_text = self.new_password_le.text()
        confirm_text = self.confirm_password_le.text()
        try:
            check_password_integrity(pw_text, confirm_text)
        except Exception as e:
            QMessageBox.warning(self,
                                "Error Message",
                                str(e),
                                QMessageBox.Close)
        else:
            self.new_password_le.setEnabled(False)
            self.confirm_password_le.setEnabled(False)
            self.password_check_btn.setEnabled(False)
            self.ok_button.setEnabled(True)

    def accept_user_info(self):
        """Verify that the user's passwords match. If so, save the user's
        info to DB and display the login window."""
        user_name_text = self.user_name_le.text()
        pw_text = self.new_password_le.text()
        hashed_pw = encrypt_password(pw_text)
        # postgresql only accepts hexadecimal format
        hashed_pw_qbyte = QByteArray(hashed_pw)
        input_db_record = {
            'user_password': hashed_pw_qbyte,
        }
        # self.insert_user_info(input_db_record)
        where_clause = f"user_name = '{user_name_text}'"
        self.db_util.update_db('users', input_db_record, where_clause)
        self.user_input_dialog.close()
