import sys
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QCloseEvent
from di_lab import Lab
from item_model import ItemModel


class ItemWidgetMapper(QWidget):
    def __init__(self, model: ItemModel,
                 indexes: List[QModelIndex] = None,
                 parent=None):
        super().__init__(parent)
        self.model = model
        self.model_indexes = indexes

        self.nameLabel = QLabel("제품명:")
        self.nameLineEdit = QLineEdit()

        self.validLabel = QLabel("유효:")
        self.validComboBox = QComboBox()
        self.validComboBox.addItems(['True', 'False'])

        self.categoryLabel = QLabel("제품군:")
        self.categoryComboBox = QComboBox()
        category_items = list(Lab().categories.values())
        self.categoryComboBox.addItems(category_items)

        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QTextEdit()

        self.nextButton = QPushButton("&Next")
        self.previousButton = QPushButton("&Previous")

        self.okButton = QPushButton("&Ok")
        self.cancelButton = QPushButton("&Cancel")

        self.nameLabel.setBuddy(self.nameLineEdit)
        self.validLabel.setBuddy(self.validComboBox)
        self.categoryLabel.setBuddy(self.categoryComboBox)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()

        self.save_flag = False

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.validComboBox, 1)
        self.mapper.addMapping(self.nameLineEdit, 2)
        self.mapper.addMapping(self.categoryComboBox, 3)
        self.mapper.addMapping(self.descriptionTextEdit, 4)

        self.previousButton.clicked.connect(self.mapper.toPrevious)
        self.nextButton.clicked.connect(self.mapper.toNext)
        self.mapper.currentIndexChanged.connect(self.updateButtons)

        self.okButton.clicked.connect(self.ok_clicked)
        self.cancelButton.clicked.connect(self.cancel_clicked)

        if self.model_indexes is None:
            self.mapper.toLast()
        else:
            self.mapper.setCurrentIndex(self.model_indexes[0].row())

    def updateButtons(self, row):
        if self.model_indexes is None:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
        else:
            self.previousButton.setEnabled(row > self.model_indexes[0].row())
            self.nextButton.setEnabled(row < self.model_indexes[-1].row())

    def ok_clicked(self):
        self.save_flag = True
        self.close()

    def cancel_clicked(self):
        self.save_flag = False
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.save_flag:
            pass
        else:
            self.model.cancel_add_new_row()
        super().closeEvent(event)

    def initializeUI(self):
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.okButton, Qt.AlignTop)
        vbox1.addWidget(self.cancelButton)
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
    window = ItemWidgetMapper(model)
    sys.exit(app.exec())
