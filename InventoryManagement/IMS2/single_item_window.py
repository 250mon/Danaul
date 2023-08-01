import sys, os
import pandas as pd
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from di_lab import Lab
from item_model import ItemModel
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class SingleItemWindow(QWidget):
    add_item_signal = Signal(object)
    chg_item_signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel,
                 indexes: List[QModelIndex] or QModelIndex,
                 parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model

        # if the selected index is a single index, it means
        # that we are editing a newly added item here.
        if isinstance(indexes, List):
            logger.debug("SingleItemWindow: change items mode")
            self.new_item_mode = False
            self.model_indexes = indexes
        else:
            logger.debug("SingleItemWindow: new item mode")
            self.new_item_mode = True
            self.model_indexes = [indexes]

        self.nameLabel = QLabel("제품명:")
        self.nameLineEdit = QLineEdit()
        if not self.new_item_mode:
            self.nameLineEdit.setReadOnly(True)

        self.validLabel = QLabel("유효:")
        self.validComboBox = QComboBox()
        self.validComboBox.addItems(['True', 'False'])
        if 'item_valid' not in self.proxy_model.sourceModel().editable_col_iloc.keys():
            self.validComboBox.setEnabled(False)

        self.categoryLabel = QLabel("제품군:")
        self.categoryComboBox = QComboBox()
        category_name_list = Lab().table_df['category']['category_name'].values.tolist()
        self.categoryComboBox.addItems(category_name_list)

        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QPlainTextEdit()

        self.nextButton = QPushButton("&Next")
        self.previousButton = QPushButton("&Previous")

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        self.nameLabel.setBuddy(self.nameLineEdit)
        self.validLabel.setBuddy(self.validComboBox)
        self.categoryLabel.setBuddy(self.categoryComboBox)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_item_by_single_item_window"):
            self.add_item_signal.connect(self.parent.added_new_item_by_single_item_window)
        if hasattr(self.parent, "changed_items_by_single_item_window"):
            self.chg_item_signal.connect(self.parent.changed_items_by_single_item_window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.validComboBox, 1)
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
        if self.model_indexes is None:
            self.mapper.toLast()
        else:
            self.mapper.setCurrentIndex(self.model_indexes[0].row())

    def updateButtons(self, row):
        if self.new_item_mode:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
        else:
            self.previousButton.setEnabled(row > self.model_indexes[0].row())
            self.nextButton.setEnabled(row < self.model_indexes[-1].row())

    def ok_clicked(self):
        if self.new_item_mode:
            logger.debug(f'Added Item Index: {self.model_indexes[0]}')
            self.mapper.submit()
            self.add_item_signal.emit(self.model_indexes[0])
        else:
            logger.debug(f'Changed Items Indexes: {self.model_indexes}')
            self.mapper.submit()
            self.chg_item_signal.emit(self.model_indexes)
        # adding a new item

    def exit_clicked(self):
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
        gridbox.addWidget(self.nameLineEdit, 0, 1, 1, 1)
        gridbox.addWidget(self.categoryLabel, 1, 0, 1, 1)
        gridbox.addWidget(self.categoryComboBox, 1, 1, 1, 1)
        gridbox.addWidget(self.descriptionLabel, 3, 0, 1, 1, Qt.AlignTop)
        gridbox.addWidget(self.descriptionTextEdit, 3, 1, 1, 1)
        gridbox.addLayout(vbox1, 3, 2, 1, 1)
        gridbox.addWidget(self.validLabel, 4, 0, 1, 1)
        gridbox.addWidget(self.validComboBox, 4, 1, 1, 1)
        gridbox.addLayout(hbox1, 5, 1, 1, 1)

        self.setLayout(gridbox)
        self.setWindowTitle("아이템 입력")
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = ItemModel()
    window = SingleItemWindow(model)
    sys.exit(app.exec())
