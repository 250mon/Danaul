from PySide6.QtWidgets import (
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QComboBox, QPlainTextEdit,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from model.modality_model import ModalityModel


class NewModalityDialog(QDialog):
    new_modality_signal = Signal(object)

    def __init__(self, src_model: ModalityModel, parent):
        super().__init__(parent)
        self.source_model = src_model
        self.init_ui()

    def init_ui(self):
        """ Set up the dialog box for the modality to create a new modality. """
        self.setWindowTitle("Create New Modality")

        self.modality_name_le = QLineEdit()
        modality_name_btn = QPushButton("중복확인")
        modality_name_btn.clicked.connect(self.check_duplicate_modality_name)
        modality_name_hbox = QHBoxLayout()
        modality_name_hbox.addWidget(self.modality_name_le)
        modality_name_hbox.addWidget(modality_name_btn)

        self.modality_price_le = QLineEdit()
        self.modality_price_le.setInputMask("9999999")
        self.category_cb = QComboBox()
        self.description_te = QPlainTextEdit()

        # initially disabled
        self.modality_price_le.setEnabled(False)
        self.category_cb.setEnabled(False)
        self.description_te.setEnabled(False)

        # Arrange QLineEdit widgets in a QFormLayout
        dialog_form = QFormLayout()
        dialog_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        dialog_form.addRow("치료이름", modality_name_hbox)
        dialog_form.addRow("가   격", self.modality_price_le)
        dialog_form.addRow("분   류", self.category_cb)
        dialog_form.addRow("비   고", self.description_te)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_modality_info)

        dialog_v_box = QVBoxLayout()
        dialog_v_box.setAlignment(Qt.AlignTop)
        dialog_v_box.addSpacing(10)
        dialog_v_box.addLayout(dialog_form, 1)
        dialog_v_box.addWidget(ok_button)

        self.setLayout(dialog_v_box)

    def update_with_latest_model(self):
        self.initialize_form()

        combo_info_dict = self.source_model.get_combobox_delegate_info()
        category_list = combo_info_dict.get(self.source_model.get_col_number('category_name'))
        self.category_cb.addItems(category_list)

    def initialize_form(self):
        self.modality_name_le.clear()
        self.modality_price_le.clear()
        self.category_cb.clear()
        self.description_te.clear()

    def check_duplicate_modality_name(self):
        modality_name = self.modality_name_le.text()
        if not self.source_model.is_modality_name_duplicate(modality_name):
            self.modality_name_le.setEnabled(False)
            self.modality_price_le.setEnabled(True)
            self.category_cb.setEnabled(True)
            self.description_te.setEnabled(True)
        else:
            QMessageBox.information(self,
                                    'Duplicate Modality Name',
                                    'The same Modality Name exists',
                                    QMessageBox.Close)

    def accept_modality_info(self):
        modality_name = self.modality_name_le.text()
        modality_price = int(self.modality_price_le.text())
        category = self.category_cb.currentText()
        description = self.description_te.toPlainText()

        input_db_record = {
            'modality_name': modality_name,
            'modality_price': modality_price,
            'category_name': category,
            'description': description,
        }
        self.new_modality_signal.emit(input_db_record)
        self.close()
