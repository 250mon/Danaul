import sys, os
import pandas as pd
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QSpinBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from di_lab import Lab
from item_model import ItemModel
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class SingleTrWindow(QWidget):
    create_tr_signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel,
                 index: QModelIndex,
                 parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model
        self.model_index = index

        self.nameLabel = QLabel("제품명:")
        self.nameBox = QLabel()
        self.trTypeLabel = QLabel("거래구분:")
        self.trTypeBox = QLabel()
        self.qtyLabel = QLabel("수량:")
        self.qtySpinBox = QSpinBox(1, 1000)
        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QPlainTextEdit()

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        self.nameLabel.setBuddy(self.nameBox)
        self.trTypeLabel.setBuddy(self.trTypeBox)
        self.qtyLabel.setBuddy(self.qtySpinBox)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_tr_by_single_item_window"):
            self.create_tr_signal.connect(self.parent.added_new_tr_by_single_item_window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.nameBox, 2)
        self.mapper.addMapping(self.qtySpinBox, 3)
        self.mapper.addMapping(self.descriptionTextEdit, 4)

        self.okButton.clicked.connect(self.ok_clicked)
        self.exitButton.clicked.connect(self.exit_clicked)

        self.mapper.toLast()

    def ok_clicked(self):
        logger.debug(f'Create Transaction Index: {self.model_index}')
        self.mapper.submit()
        self.create_tr_signal.emit(self.model_index)
        self.close()

    def exit_clicked(self):
        # self.create_tr_signal.emit(self.model_index)
        self.close()

    def initializeUI(self):
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.okButton, Qt.AlignTop)
        vbox1.addWidget(self.exitButton)
        vbox1.addStretch()

        hbox1 = QHBoxLayout()

        gridbox = QGridLayout()
        gridbox.addWidget(self.nameLabel, 0, 0, 1, 1)
        gridbox.addWidget(self.nameBox, 0, 1, 1, 1)
        gridbox.addWidget(self.qtyLabel, 1, 0, 1, 1)
        gridbox.addWidget(self.qtySpinBox, 1, 1, 1, 1)
        gridbox.addWidget(self.descriptionLabel, 2, 0, 1, 1, Qt.AlignTop)
        gridbox.addWidget(self.descriptionTextEdit, 2, 1, 1, 1)

        self.setLayout(gridbox)
        self.setWindowTitle("거래 입력")
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = TrModel()
    window = SingleTrWindow(model)
    sys.exit(app.exec())
