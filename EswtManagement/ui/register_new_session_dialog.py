from PySide6.QtWidgets import (
    QDialog, QLabel, QFormLayout, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal
from model.session_model import SessionModel
from common.d_logger import Logs


logger = Logs().get_logger("main")


class NewSessionDialog(QDialog):
    new_session_signal = Signal(object)

    def __init__(self, src_model: SessionModel, parent):
        super().__init__(parent)
        self.source_model = src_model
        self.patient_emr_id: int or None = None
        self.init_ui()

    def init_ui(self):
        if self.source_model is None or self.patient_emr_id is None:
            self.close()

        """ Set up the dialog box for the session to create a new session. """
        self.setWindowTitle("Create New Session")

        emrIdLabel = QLabel(self.patient_emr_id)
        self.provider_cb = QComboBox()
        self.modality_cb = QComboBox()
        self.part_cb = QComboBox()
        self.description_te = QPlainTextEdit()

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("환자 번호", emrIdLabel)
        dialog_form.addRow("치 료 사", self.provider_cb)
        dialog_form.addRow("치료 형태", self.modality_cb)
        dialog_form.addRow("부    위", self.part_cb)
        dialog_form.addRow("비    고", self.description_te)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_session_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.setLayout(dialog_v_box)

    def update_with_latest_model(self):
        self.patient_emr_id = self.source_model.selected_id

        self.initialize_form()
        combo_info_dict = self.source_model.get_combobox_delegate_info()
        provider_list = combo_info_dict.get(self.source_model.get_col_number('provider_name'))
        modality_list = combo_info_dict.get(self.source_model.get_col_number('modality_name'))
        part_list = combo_info_dict.get(self.source_model.get_col_number('part_name'))
        self.provider_cb.addItems(provider_list)
        self.modality_cb.addItems(modality_list)
        self.part_cb.addItems(part_list)

    def initialize_form(self):
        self.provider_cb.clear()
        self.modality_cb.clear()
        self.part_cb.clear()
        self.description_te.clear()

    def accept_session_info(self):
        """Verify that the session's passwords match. If so, save the session's
        info to DB and display the login window."""
        provider_name = self.provider_cb.currentText()
        modality_name = self.modality_cb.currentText()
        part_name = self.part_cb.currentText()
        description = self.description_te.toPlainText()

        input_db_record = {
            'provider_name': provider_name,
            'modality_name': modality_name,
            'part_name': part_name,
            'description': description,
        }
        self.new_session_signal.emit(input_db_record)
        self.close()
