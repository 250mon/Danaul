import pandas as pd
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLineEdit, QSplitter,
    QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QByteArray
from db.db_utils import QtDbUtil
from db.ds_lab import Lab
from common.auth_util import *



class NewUserDialog(QDialog):

    def __init__(self, db_util: QtDbUtil, parent=None):
        self.db_util = db_util
        super().__init__(parent)

    def register_new_user(self):
        """ Set up the dialog box for the user to create a new user account. """
        self.hide()  # Hide the login window
        self.user_input_dialog = QDialog(self)
        # create a new user account
        self.user_input_dialog.setWindowTitle("Create New User")

        self.user_name_le = QLineEdit()
        user_name_check_btn = QPushButton("중복확인")
        user_name_check_btn.clicked.connect(self.check_duplicate_user_name)
        user_name_hbox = QHBoxLayout()
        user_name_hbox.addWidget(self.user_name_le)
        user_name_hbox.addWidget(user_name_check_btn)

        self.new_password_le = QLineEdit()
        self.new_password_le.setEchoMode(QLineEdit.Password)
        self.confirm_password_le = QLineEdit()
        self.confirm_password_le.setEchoMode(QLineEdit.Password)
        self.password_check_btn = QPushButton("확인")
        self.password_check_btn.clicked.connect(self.check_password_btn_clicked)
        pasword_hbox = QHBoxLayout()
        pasword_hbox.addWidget(self.confirm_password_le)
        pasword_hbox.addWidget(self.password_check_btn)

        # additional info
        self.real_name_le = QLineEdit()
        self.job_cb = QComboBox()
        self.job_cb.addItems(['물리치료', '도수치료', '간호', '방사선', '진료'])

        # initially disabled
        self.new_password_le.setEnabled(False)
        self.confirm_password_le.setEnabled(False)
        self.password_check_btn.setEnabled(False)
        self.real_name_le.setEnabled(False)
        self.job_cb.setEnabled(False)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("아이디", user_name_hbox)
        dialog_form.addRow("비밀번호 입력", self.new_password_le)
        dialog_form.addRow("비밀번호 확인", pasword_hbox)
        dialog_form.addRow("이 름", self.real_name_le)
        dialog_form.addRow("직 무", self.job_cb)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_user_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

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
            self.real_name_le.setEnabled(True)
            self.job_cb.setEnabled(True)

    def accept_user_info(self):
        """Verify that the user's passwords match. If so, save the user's
        info to DB and display the login window."""
        user_name = self.user_name_le.text()

        pw_text = self.new_password_le.text()
        hashed_pw = encrypt_password(pw_text)
        # postgresql only accepts hexadecimal format
        hashed_pw_qbyte = QByteArray(hashed_pw)

        real_name = self.real_name_le.text()
        if len(real_name) < 1:
            return

        job = self.job_cb.currentText()

        input_db_record = {
            'active': True,
            'user_name': user_name,
            'user_password': hashed_pw_qbyte,
            'user_realname': real_name,
            'user_job': job,
        }
        # self.insert_user_info(input_db_record)
        self.db_util.insert_into_db('users', input_db_record)
        self.user_input_dialog.close()

    def check_duplicate_user_name(self):
        user_name = self.user_name_le.text()
        if not self.is_user_name_duplicate(user_name):
            self.user_name_le.setEnabled(False)
            self.new_password_le.setEnabled(True)
            self.confirm_password_le.setEnabled(True)
            self.password_check_btn.setEnabled(True)
        else:
            QMessageBox.information(self,
                                    'Duplicate User Name',
                                    'The same User Name exists',
                                    QMessageBox.Close)

    def is_user_name_duplicate(self, user_name: str):
        users_df: pd.DataFrame = Lab().table_df['users']
        if (users_df.empty or
                users_df.query(f"user_name == '{user_name}'").empty):
            return False
        else:
            return True
