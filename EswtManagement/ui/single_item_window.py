import sys, os
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from db.ds_lab import Lab
from model.treatment_model import TreatmentModel
from common.d_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class Singletreatments.indow(QWidget):
    add_treatments.signal = Signal(object)
    chg_treatments.signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel,
                 indexes: List[QModelIndex] or QModelIndex,
                 parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model

        # if the selected index is a single index, it means
        # that we are editing a newly added treatments.here.
        if isinstance(indexes, List):
            logger.debug("change treatments mode")
            self.new_treatments.mode = False
            self.model_indexes = indexes
        else:
            logger.debug("new treatments.mode")
            self.new_treatments.mode = True
            self.model_indexes = [indexes]

        self.nameLabel = QLabel("제품명:")
        if self.new_treatments.mode:
            self.nameLineEdit = QLineEdit()
            # self.nameLineEdit.setReadOnly(True)
        else:
            self.nameBox = QLabel()

        self.activeLabel = QLabel("활성:")
        self.activeComboBox = QComboBox()
        self.activeComboBox.addtreatments(['True', 'False'])
        if 'active' not in self.proxy_model.sourceModel().editable_col_dicts.keys():
            self.activeComboBox.setEnabled(False)

        self.categoryLabel = QLabel("제품군:")
        self.categoryComboBox = QComboBox()
        category_name_list = Lab().table_df['category']['category_name'].values.tolist()
        self.categoryComboBox.addtreatments(category_name_list)

        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QPlainTextEdit()

        self.nextButton = QPushButton("&Next")
        self.previousButton = QPushButton("&Previous")

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        if self.new_treatments.mode:
            self.nameLabel.setBuddy(self.nameLineEdit)
        else:
            self.nameLabel.setBuddy(self.nameBox)
        self.activeLabel.setBuddy(self.activeComboBox)
        self.categoryLabel.setBuddy(self.categoryComboBox)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_treatments.by_single_treatments.window"):
            self.add_treatments.signal.connect(self.parent.added_new_treatments.by_single_treatments.window)
        if hasattr(self.parent, "changed_treatments_by_single_treatments.window"):
            self.chg_treatments.signal.connect(self.parent.changed_treatments_by_single_treatments.window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.activeComboBox, 1)
        if self.new_treatments.mode:
            self.mapper.addMapping(self.nameLineEdit, 2)
        self.mapper.addMapping(self.categoryComboBox, 3)
        self.mapper.addMapping(self.descriptionTextEdit, 4)

        self.previousButton.clicked.connect(self.mapper.toPrevious)
        self.nextButton.clicked.connect(self.mapper.toNext)
        self.mapper.currentIndexChanged.connect(self.updateButtons)

        self.okButton.clicked.connect(self.ok_clicked)
        self.exitButton.clicked.connect(self.exit_clicked)

        # if model_indexes is not given, it means adding a new row
        # otherwise the rows of model_indexes are being modified
        if self.new_treatments.mode:
            self.mapper.toLast()
        else:
            self.mapper.setCurrentIndex(self.model_indexes[0].row())

    def updateButtons(self, row):
        if self.new_treatments.mode:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
        else:
            name_col = self.proxy_model.sourceModel().get_col_number('treatment_name')
            self.nameBox.setText(self.proxy_model.index(row, name_col).data())
            self.previousButton.setEnabled(row > self.model_indexes[0].row())
            self.nextButton.setEnabled(row < self.model_indexes[-1].row())

    def ok_clicked(self):
        if self.new_treatments.mode:
            logger.debug(f"Added treatments.Index: {self.model_indexes[0]}")
            self.mapper.submit()
            self.add_treatments.signal.emit(self.model_indexes[0])
        else:
            logger.debug(f"Changed treatments Indexes: {self.model_indexes}")
            self.mapper.submit()
            self.chg_treatments.signal.emit(self.model_indexes)
        # adding a new item

    def exit_clicked(self):
        if self.new_treatments.mode:
            self.add_treatments.signal.emit(self.model_indexes[0])
        self.close()

    def initializeUI(self):
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.okButton, Qt.AlignTop)
        vbox1.addWidget(self.exitButton)
        vbox1.addStretch()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.previousButton)
        hbox1.addWidget(self.nextButton)

        gridbox = QGridLayout()
        gridbox.addWidget(self.nameLabel, 0, 0, 1, 1)
        if self.new_treatments.mode:
            gridbox.addWidget(self.nameLineEdit, 0, 1, 1, 1)
        else:
            gridbox.addWidget(self.nameBox, 0, 1, 1, 1)
        gridbox.addWidget(self.categoryLabel, 1, 0, 1, 1)
        gridbox.addWidget(self.categoryComboBox, 1, 1, 1, 1)
        gridbox.addWidget(self.descriptionLabel, 3, 0, 1, 1, Qt.AlignTop)
        gridbox.addWidget(self.descriptionTextEdit, 3, 1, 1, 1)
        gridbox.addWidget(self.activeLabel, 4, 0, 1, 1)
        gridbox.addWidget(self.activeComboBox, 4, 1, 1, 1)

        gridbox.addLayout(vbox1, 3, 2, 1, 1)
        gridbox.addLayout(hbox1, 5, 1, 1, 1)

        self.setLayout(gridbox)
        self.setWindowTitle("아이템 입력")
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = TreatmentModel()
    window = Singletreatments.indow(model)
    sys.exit(app.exec())
