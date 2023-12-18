from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from model.patient_model import PatientModel


class NewPatientDialog(QDialog):
    new_patient_signal = Signal(object)

    def __init__(self, src_model: PatientModel, parent):
        super().__init__(parent)
        self.source_model = src_model
        self.new_patient_signal.connect(parent.save_model_to_db)
        self.init_ui()

    def init_ui(self):
        """ Set up the dialog box for the patient to create a new patient. """
        self.setWindowTitle("Create New Patient")

        self.emr_id_le = QLineEdit()
        self.emr_id_le.setInputMask("99999")
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

        self.setLayout(dialog_v_box)

    def update_with_latest_model(self):
        self.initialize_form()

    def initialize_form(self):
        self.emr_id_le.clear()
        self.name_le.clear()

    def start_with_emr_id(self, emr_id: int):
        self.emr_id_le.setText(emr_id)
        self.name_le.clear()
        self.emr_id_le.setEnabled(False)
        self.name_le.setEnabled(True)
        self.gender_cb.setEnabled(True)

    def check_duplicate_emr_id(self):
        emr_id = int(self.emr_id_le.text())
        if not self.source_model.is_emr_id_duplicate(emr_id):
            self.emr_id_le.setEnabled(False)
            self.name_le.setEnabled(True)
            self.gender_cb.setEnabled(True)
        else:
            QMessageBox.information(self,
                                    'Duplicate EMR ID',
                                    'The same EMR ID exists',
                                    QMessageBox.Close)

    def accept_patient_info(self):
        """Verify that the patient's passwords match. If so, save the patient's
        info to DB and display the login window."""
        emr_id = int(self.emr_id_le.text())
        name = self.name_le.text()
        gender = self.gender_cb.currentText()

        input_db_record = {
            'patient_emr_id': emr_id,
            'patient_name': name,
            'patient_gender': gender,
        }
        self.new_patient_signal.emit(input_db_record)
        self.close()
