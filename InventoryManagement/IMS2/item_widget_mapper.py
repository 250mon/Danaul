import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from di_lab import Lab


class ItemWidgetMapper(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

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

    def updateButtons(self, row):
        self.previousButton.setEnabled(row > 0)
        self.nextButton.setEnabled(row < self.model.rowCount() - 1)

    def initializeUI(self):
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        hbox3 = QHBoxLayout()
        hbox4 = QHBoxLayout()
        hbox5 = QHBoxLayout()

        hbox1.addWidget(self.nameLabel)
        hbox1.addWidget(self.nameLineEdit)
        hbox2.addWidget(self.categoryLabel)
        hbox2.addWidget(self.categoryComboBox)
        hbox3.addWidget(self.descriptionLabel)
        hbox3.addWidget(self.descriptionTextEdit)
        hbox4.addWidget(self.validLabel)
        hbox4.addWidget(self.validComboBox)
        hbox5.addWidget(self.nextButton)
        hbox5.addWidget(self.previousButton)
        hbox5.addWidget(self.okButton)
        hbox5.addWidget(self.cancelButton)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox5)


        # layout = QGridLayout()
        # layout.addWidget(self.nameLabel, 0, 0, 1, 1)
        # layout.addWidget(self.nameLineEdit, 0, 1, 1, 1)
        # layout.addWidget(self.previousButton, 0, 2, 1, 1)
        # layout.addWidget(self.categoryLabel, 1, 0, 1, 1)
        # layout.addWidget(self.categoryComboBox, 1, 1, 1, 1)
        # layout.addWidget(self.nextButton, 1, 2, 1, 1)
        # layout.addWidget(self.descriptionLabel, 3, 0, 1, 1)
        # layout.addWidget(self.descriptionTextEdit, 3, 1, 1, 1)
        # layout.addWidget(self.validLabel, 4, 0, 1, 1)
        # layout.addWidget(self.validComboBox, 4, 1, 1, 1)
        #
        # vbox = QVBoxLayout()
        # vbox.addWidget(self.okButton)
        # vbox.addWidget(self.cancelButton)
        # layout.addLayout(vbox, 3, 2, 1, 1)
        #
        # self.setLayout(layout)
        self.setLayout(vbox)

        self.setWindowTitle("아이템 입력")
        self.mapper.toLast()

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ItemWidgetMapper()
    sys.exit(app.exec())
