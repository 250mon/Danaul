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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_model: SessionModel or None = None
        self.patient_emr_id: int or None = None
        self.provider_list = []
        self.modality_list = []
        self.part_list = []
        self.init_ui()
        self.new_session_signal.connect(parent.save_model_to_db)

    def set_source_model(self, src_model: SessionModel):
        self.source_model = src_model
        self.patient_emr_id = self.source_model.selected_id

        combo_info_dict = self.source_model.get_combobox_delegate_info()
        self.provider_list = combo_info_dict.get(self.source_model.get_col_number('provider_name'))
        self.modality_list = combo_info_dict.get(self.source_model.get_col_number('modality_name'))
        self.part_list = combo_info_dict.get(self.source_model.get_col_number('part_name'))
        self.providerCb.addItems(self.provider_list)
        self.modalityCb.addItems(self.modality_list)
        self.partCb.addItems(self.part_list)

    def init_ui(self):
        if self.source_model is None or self.patient_emr_id is None:
            self.close()

        """ Set up the dialog box for the session to create a new session. """
        self.setWindowTitle("Create New Session")

        emrIdLabel = QLabel(self.patient_emr_id)
        self.providerCb = QComboBox()
        self.modalityCb = QComboBox()
        self.partCb = QComboBox()
        self.descriptionTextEdit = QPlainTextEdit()

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("환자 번호", emrIdLabel)
        dialog_form.addRow("치 료 사", self.providerCb)
        dialog_form.addRow("치료 종류", self.modalityCb)
        dialog_form.addRow("부    위", self.partCb)
        dialog_form.addRow("비    고", self.descriptionTextEdit)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_session_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.setLayout(dialog_v_box)

    def accept_session_info(self):
        """Verify that the session's passwords match. If so, save the session's
        info to DB and display the login window."""
        provider_name = self.providerCb.currentText()
        modality_name = self.modalityCb.currentText()
        part_name = self.partCb.currentText()

        input_db_record = {
            'provider_name': provider_name,
            'modality_name': modality_name,
            'part_name': part_name,
        }
        self.new_session_signal.emit(input_db_record)
        self.close()
