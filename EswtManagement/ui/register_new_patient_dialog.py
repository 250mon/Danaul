from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt
from db.db_utils import QtDbUtil


class RegNewPatientDialog(QDialog):

    def __init__(self, db_util: QtDbUtil, parent=None):
        self.db_util = db_util
        super().__init__(parent)

    def register_new_patient(self):
        """ Set up the dialog box for the patient to create a new patient. """
        self.hide()  # Hide the login window
        self.patient_input_dialog = QDialog(self)
        # create a new patient
        self.patient_input_dialog.setWindowTitle("Create New Patient")

        self.emr_id_le = QLineEdit()
        self.emr_id_le.setInputMask("9")
        emr_id_check_btn = QPushButton("중복확인")
        emr_id_check_btn.clicked.connect(self.check_duplicate_emr_id)
        patient_emr_id_hbox = QHBoxLayout()
        patient_emr_id_hbox.addWidget(self.emr_id_le)
        patient_emr_id_hbox.addWidget(emr_id_check_btn)

        self.name_le = QLineEdit()
        self.gender_cb = QComboBox()
        self.gender_cb.addItems(["M", "F"])

        # initially disabled
        self.name_le.setEnabled(False)
        self.gender_cb.setEnabled(False)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("환자번호", patient_emr_id_hbox)
        dialog_form.addRow("이   름", self.name_le)
        dialog_form.addRow("성   별", self.gender_cb)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_patient_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.patient_input_dialog.setLayout(dialog_v_box)
        self.patient_input_dialog.show()

    def check_duplicate_emr_id(self):
        # TODO: check if emr_id is already in use
        self.emr_id_le.setEnabled(False)
        self.name_le.setEnabled(True)
        self.gender_cb.setEnabled(True)

    def accept_patient_info(self):
        """Verify that the patient's passwords match. If so, save the patient's
        info to DB and display the login window."""
        emr_id = self.emr_id_le.text()
        name = self.name_le.text()
        gender = self.gender_cb.currentText()

        input_db_record = {
            'patient_emr_id': emr_id,
            'patient_name': name,
            'patient_gender': gender,
        }
        # self.insert_patient_info(input_db_record)
        self.db_util.insert_into_db('patients', input_db_record)
        self.patient_input_dialog.close()

        # TODO: update the patient list of main widget
