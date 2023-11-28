import sys
from typing import List
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit,
    QPushButton, QDataWidgetMapper, QGridLayout
)
from PySide6.QtCore import Qt, QModelIndex, Signal, QSortFilterProxyModel
from db.ds_lab import Lab
from model.patient_model import PatientModel
from common.d_logger import Logs


logger = Logs().get_logger("main")


class SinglePatientWindow(QWidget):
    add_patient_signal = Signal(object)
    chg_patient_signal = Signal(object)

    def __init__(self, proxy_model: QSortFilterProxyModel,
                 indexes: List[QModelIndex] or QModelIndex,
                 parent=None):
        super().__init__()
        self.parent = parent
        self.proxy_model = proxy_model

        # if the selected index is a single index, it means
        # that we are editing a newly added patient here.
        if isinstance(indexes, List):
            logger.debug("change patient mode")
            self.new_patient_mode = False
            self.model_indexes = indexes
        else:
            logger.debug("new patient mode")
            self.new_patient_mode = True
            self.model_indexes = [indexes]

        self.emrIdLabel = QLabel("EMR ID:")
        if self.new_patient_mode:
            self.emrIdLineEdit = QLineEdit()
        else:
            self.emrIdBox = QLabel()

        self.nameLabel = QLabel("이   름:")
        self.nameLineEdit = QLineEdit()

        self.genderLabel = QLabel("성   별:")
        self.genderComboBox = QComboBox()
        self.genderComboBox.addItems(["M", "F"])

        self.birthDateLabel = QLabel("생년월일:")
        self.birthDateEdit = QDateEdit()

        self.nextButton = QPushButton("&Next")
        self.previousButton = QPushButton("&Previous")

        self.okButton = QPushButton("&Ok")
        self.exitButton = QPushButton("&Exit")

        if self.new_patient_mode:
            self.nameLabel.setBuddy(self.nameLineEdit)
        else:
            self.nameLabel.setBuddy(self.emrIdBox)
        self.emrIdLabel.setBuddy(self.emrIdLineEdit)
        self.genderLabel.setBuddy(self.genderComboBox)
        self.birthDateLabel.setBuddy(self.birthDateEdit)
        self.addMapper()

        # wire the signals into the parent widget
        if hasattr(self.parent, "added_new_patient_by_single_patient_window"):
            self.add_patient_signal.connect(self.parent.added_new_patient_by_single_patient_window)
        if hasattr(self.parent, "changed_patients_by_single_patient_window"):
            self.chg_patient_signal.connect(self.parent.changed_patients_by_single_patient_window)

        self.initializeUI()

    def addMapper(self):
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.proxy_model)
        self.mapper.addMapping(self.emrIdLineEdit, 1)
        if self.new_patient_mode:
            self.mapper.addMapping(self.nameLineEdit, 2)
        self.mapper.addMapping(self.genderComboBox, 3)
        self.mapper.addMapping(self.birthDateEdit, 4)

        self.previousButton.clicked.connect(self.mapper.toPrevious)
        self.nextButton.clicked.connect(self.mapper.toNext)
        self.mapper.currentIndexChanged.connect(self.updateButtons)

        self.okButton.clicked.connect(self.ok_clicked)
        self.exitButton.clicked.connect(self.exit_clicked)

        # if model_indexes is not given, it means adding a new row
        # otherwise the rows of model_indexes are being modified
        if self.new_patient_mode:
            self.mapper.toLast()
        else:
            self.mapper.setCurrentIndex(self.model_indexes[0].row())

    def updateButtons(self, row):
        if self.new_patient_mode:
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(False)
        else:
            name_col = self.proxy_model.sourceModel().get_col_number('treatment_name')
            self.emrIdBox.setText(self.proxy_model.index(row, name_col).data())
            self.previousButton.setEnabled(row > self.model_indexes[0].row())
            self.nextButton.setEnabled(row < self.model_indexes[-1].row())

    def ok_clicked(self):
        if self.new_patient_mode:
            logger.debug(f"Added Patient_Index: {self.model_indexes[0]}")
            self.mapper.submit()
            self.add_patient_signal.emit(self.model_indexes[0])
        else:
            logger.debug(f"Changed Patients Indexes: {self.model_indexes}")
            self.mapper.submit()
            self.chg_patient_signal.emit(self.model_indexes)
        # adding a new patient

    def exit_clicked(self):
        if self.new_patient_mode:
            self.add_patient_signal.emit(self.model_indexes[0])
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
        gridbox.addWidget(self.emrIdLabel, 0, 0, 1, 1)
        if self.new_patient_mode:
            gridbox.addWidget(self.emrIdLineEdit, 0, 1, 1, 1)
        else:
            gridbox.addWidget(self.emrIdBox, 0, 1, 1, 1)
        gridbox.addWidget(self.nameLabel, 1, 0, 1, 1)
        gridbox.addWidget(self.nameLineEdit, 1, 1, 1, 1)
        gridbox.addWidget(self.genderLabel, 4, 0, 1, 1)
        gridbox.addWidget(self.genderComboBox, 4, 1, 1, 1)
        gridbox.addWidget(self.birthDateLabel, 3, 0, 1, 1)
        gridbox.addWidget(self.birthDateEdit, 3, 1, 1, 1)

        gridbox.addLayout(vbox1, 3, 2, 1, 1)
        gridbox.addLayout(hbox1, 5, 1, 1, 1)

        self.setLayout(gridbox)
        self.setWindowTitle("환자 입력")
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = PatientModel("Admin")
    window = SinglePatientWindow(model, QModelIndex())
    sys.exit(app.exec())
