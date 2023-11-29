import sys
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QDataWidgetMapper
)
from PySide6.QtCore import QModelIndex, Signal, QSortFilterProxyModel
from model.provider_model import ProviderModel
from common.d_logger import Logs


logger = Logs().get_logger("main")


class SingleProviderWindow(QWidget):
    add_provider_signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel,
                 indexes: List[QModelIndex] or QModelIndex,
                 parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model

        # if the selected index is a single index, it means
        # that we are editing a newly added provider here.
        self.model_indexes = [indexes]

        self.nameLabel = QLabel("이   름:")
        self.nameLineEdit = QLineEdit()

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        self.nameLabel.setBuddy(self.nameLineEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_provider_by_single_provider_window"):
            self.add_provider_signal.connect(self.parent.added_new_provider_by_single_provider_window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.nameLineEdit, 1)

        self.okButton.clicked.connect(self.ok_clicked)
        self.exitButton.clicked.connect(self.exit_clicked)

        # if model_indexes is not given, it means adding a new row
        # otherwise the rows of model_indexes are being modified
        self.mapper.toLast()

    def ok_clicked(self):
        logger.debug(f"Added Provider_Index: {self.model_indexes[0]}")
        self.mapper.submit()
        self.add_provider_signal.emit(self.model_indexes[0])
        self.close()

    def exit_clicked(self):
        self.add_provider_signal.emit(self.model_indexes[0])
        self.close()

    def initializeUI(self):
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.nameLabel)
        hbox1.addWidget(self.nameLineEdit)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.okButton)
        hbox2.addWidget(self.exitButton)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
        self.setMinimumWidth(250)
        self.setWindowTitle("치료사 입력")
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = ProviderModel("Admin")
    window = SingleProviderWindow(model, QModelIndex())
    sys.exit(app.exec())
