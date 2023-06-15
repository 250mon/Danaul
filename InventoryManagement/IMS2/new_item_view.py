import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QRadioButton,
    QVBoxLayout, QSpinBox, QLabel, QLineEdit, QTextEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)


class ItemWidget(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model

        self.nameLabel = QLabel("아이템명:")
        self.nameLineEdit = QLineEdit()

        self.validityLabel = QLabel("유효:")
        self.validRadioButton = QRadioButton("사용")
        self.invalidRadioButton = QRadioButton("폐기")
        self.validRadioButton.setChecked(True)

        self.categoryLabel = QLabel("제품군:")
        self.categorySpinBox = QSpinBox()

        self.descriptionLabel = QLabel("비고:")
        self.descriptionTextEdit = QTextEdit()

        self.nextButton = QPushButton("&Next")
        self.previousButton = QPushButton("&Previous")

        self.nameLabel.setBuddy(self.nameLineEdit)
        self.validityLabel.setBuddy(self.validitySpinBox)
        self.categoryLabel.setBuddy(self.categorySpinBox)
        self.descriptionLabel.setBuddy(self.descriptionTextEdit)
        self.addMapper()
        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.nameLineEdit, 1)
        self.mapper.addMapping(self.categorySpinBox, 2)
        self.mapper.addMapping(self.descriptionTextEdit, 3)

        self.previousButton.clicked.connect(self.mapper.toPrevious)
        self.nextButton.clicked.connect(self.mapper.toNext)
        self.mapper.currentIndexChanged.connect(self.updateButtons)

    def updateButtons(self, row):
        self.previousButton.setEnabled(row > 0)
        self.nextButton.setEnabled(row < self.model.rowCount() - 1)

    def initializeUI(self):
        layout = QGridLayout()
        layout.addWidget(self.nameLabel, 0, 0, 1, 1)
        layout.addWidget(self.nameEdit, 0, 1, 1, 1)
        layout.addWidget(self.previousButton, 0, 2, 1, 1)
        layout.addWidget(self.addressLabel, 1, 0, 1, 1)
        layout.addWidget(self.addressEdit, 1, 1, 2, 1)
        layout.addWidget(self.nextButton, 1, 2, 1, 1)
        layout.addWidget(self.ageLabel, 3, 0, 1, 1)
        layout.addWidget(self.ageSpinBox, 3, 1, 1, 1)
        self.setLayout(layout)

        self.setWindowTitle("Simple Widget Mapper")
        self.mapper.toFirst()

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
