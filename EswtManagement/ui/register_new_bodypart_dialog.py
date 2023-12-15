from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from model.bodypart_model import BodyPartModel


class NewBodyPartDialog(QDialog):
    new_part_signal = Signal(object)

    def __init__(self, src_model: BodyPartModel, parent):
        super().__init__(parent)
        self.source_model = src_model
        self.new_part_signal.connect(parent.save_model_to_db)
        self.init_ui()

    def init_ui(self):
        """ Set up the dialog box for the part to create a new part. """
        self.setWindowTitle("Create New BodyPart")

        self.part_name_le = QLineEdit()
        part_name_btn = QPushButton("중복확인")
        part_name_btn.clicked.connect(self.check_duplicate_part_name)
        part_name_hbox = QHBoxLayout()
        part_name_hbox.addWidget(self.part_name_le)
        part_name_hbox.addWidget(part_name_btn)

        self.sub_parts_te = QPlainTextEdit()

        # initially disabled
        self.sub_parts_te.setEnabled(False)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("부   위", part_name_hbox)
        dialog_form.addRow("세부부위", self.sub_parts_te)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_part_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.setLayout(dialog_v_box)

    def update_with_latest_model(self):
        self.initialize_form()

    def initialize_form(self):
        self.part_name_le.clear()
        self.sub_parts_te.clear()

    def check_duplicate_part_name(self):
        part_name = self.part_name_le.text()
        if not self.source_model.is_part_name_duplicate(part_name):
            self.part_name_le.setEnabled(False)
            self.sub_parts_te.setEnabled(True)
        else:
            QMessageBox.information(self,
                                    'Duplicate Body Part Name',
                                    'The same Body Part Name exists',
                                    QMessageBox.Close)

    def accept_part_info(self):
        part_name = self.part_name_le.text()
        sub_parts = self.sub_parts_te.toPlainText()

        input_db_record = {
            'part_name': part_name,
            'sub_parts': sub_parts,
        }
        self.new_part_signal.emit(input_db_record)
        self.close()
