import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel
from model.session_model import SessionModel
from common.d_logger import Logs


logger = Logs().get_logger("main")


class SingleSessionWindow(QWidget):
    create_tr_signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel, parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model
        self.source_model: SessionModel = self.proxy_model.sourceModel()

        self.emrIdLabel = QLabel(self.source_model.selected_emr_id)
        self.nameLabel = QLabel(self.source_model.selected_name)
        self.providerLabel = QLabel("치료사:")
        self.providerCb = QComboBox()
        # TODO: provider combobox add items
        self.modalityLabel = QLabel("치료 형태:")
        self.modalityCb = QComboBox()
        # TODO: modality combobox add items
        self.partLabel = QLabel("치료 부위:")
        self.partCb = QComboBox()
        # TODO: part combobox add items

        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QPlainTextEdit()

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        self.providerLabel.setBuddy(self.providerCb)
        self.modalityLabel.setBuddy(self.modalityCb)
        self.partLabel.setBuddy(self.partCb)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_tr_by_single_tr_window"):
            self.create_tr_signal.connect(self.parent.added_new_tr_by_single_tr_window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.providerCb, self.source_model.get_col_number('provider_id'))
        self.mapper.addMapping(self.modalityCb, self.source_model.get_col_number('modality_id'))
        self.mapper.addMapping(self.partCb, self.source_model.get_col_number('part_id'))
        self.mapper.addMapping(self.descriptionTextEdit,
                               self.source_model.get_col_number('description'))

        self.okButton.clicked.connect(self.ok_clicked)
        self.exitButton.clicked.connect(self.exit_clicked)

        self.mapper.toLast()

    def ok_clicked(self):
        logger.debug(f"Created Session")
        self.mapper.submit()
        index = self.proxy_model.index(self.mapper.currentIndex(), 0)
        self.create_tr_signal.emit(index)
        self.close()

    def exit_clicked(self):
        # self.create_tr_signal.emit()
        self.close()

    def initializeUI(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.okButton)
        vbox.addWidget(self.exitButton)

        gridbox = QGridLayout()
        gridbox.addWidget(self.emrIdLabel, 0, 0, 1, 1)
        gridbox.addWidget(self.nameLabel, 0, 1, 1, 1)
        gridbox.addWidget(self.providerLabel, 1, 0, 1, 1)
        gridbox.addWidget(self.providerCb, 1, 1, 1, 1)
        gridbox.addWidget(self.modalityLabel, 2, 0, 1, 1)
        gridbox.addWidget(self.modalityCb, 2, 1, 1, 1)
        gridbox.addWidget(self.partLabel, 3, 0, 1, 1)
        gridbox.addWidget(self.partCb, 3, 1, 1, 1)

        gridbox.addLayout(vbox, 2, 2, 1, 1)

        self.setLayout(gridbox)
        self.setWindowTitle("치료 세션 입력")
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = SessionModel()
    window = SingleSessionWindow(model)
    sys.exit(app.exec())
