from typing import Dict
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QMessageBox, QWidget, QTreeView
)
from PySide6.QtCore import (
    Qt, Slot, QModelIndex, QSortFilterProxyModel
)
from PySide6.QtGui import QFont
from common.async_helper import AsyncHelper
from common.d_logger import Logs
from model.patient_model import PatientModel
from ui.item_view_helpers import ItemViewHelpers
from ui.register_new_patient_dialog import NewPatientDialog


logger = Logs().get_logger("main")


class PatientFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent)

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        index0 = self.sourceModel().index(source_row, 0, source_parent)
        index1 = self.sourceModel().index(source_row, 1, source_parent)

        result0 = self.filterRegularExpression().match(str(self.sourceModel().data(index0))).hasMatch()
        result1 = self.filterRegularExpression().match(self.sourceModel().data(index1)).hasMatch()

        return result0 or result1


class PatientWidget(QWidget):
    def __init__(self, model: PatientModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.async_helper: AsyncHelper = self.parent.async_helper
        self.source_model = model
        self.proxy_model = None
        # initialize
        self.set_model()
        self.init_ui()

    def set_model(self):
        self.proxy_model = PatientFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        # -1 means searching every column, 0 is the patient_emr_id column number
        # self.proxy_model.setFilterKeyColumn(0)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('patient_emr_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def init_ui(self):
        self.patient_view = QTreeView()
        self.item_view_helpers = ItemViewHelpers(self.source_model,
                                                 self.proxy_model,
                                                 self.patient_view,
                                                 self)
        self.patient_view.setModel(self.proxy_model)

        self.patient_view.setRootIsDecorated(False)
        self.patient_view.setAlternatingRowColors(True)
        self.patient_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.patient_view.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.patient_view.setSortingEnabled(True)
        self.patient_view.doubleClicked.connect(self.row_double_clicked)

        self.new_patient_dlg = NewPatientDialog(self.source_model, self)
        self.new_patient_dlg.new_patient_signal.connect(self.item_view_helpers.save_model_to_db)

        title_label = QLabel('환  자')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)
        refresh_btn = QPushButton('전체새로고침')
        refresh_btn.clicked.connect(self.update_all_views)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.stretch(1)
        hbox1.addWidget(refresh_btn)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText('검색어')
        self.search_bar.textChanged.connect(self.proxy_model.setFilterRegularExpression)
        self.search_bar.returnPressed.connect(self.emr_id_entered)
        add_btn = QPushButton('추 가')
        add_btn.clicked.connect(self.add_patient)
        del_btn = QPushButton('삭 제')
        del_btn.clicked.connect(self.del_patient)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(add_btn)
        edit_hbox.addWidget(del_btn)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.search_bar)
        hbox2.addStretch(1)
        hbox2.addLayout(edit_hbox)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.patient_view)
        self.setLayout(vbox)

    @Slot()
    def add_patient(self):
        logger.debug("Adding a patient ...")
        self.new_patient_dlg.update_with_latest_model()
        self.new_patient_dlg.show()

    @Slot()
    def del_patient(self):
        logger.debug("Deleting patient ...")
        if selected_indexes := self.item_view_helpers.get_selected_indexes():
            logger.debug(f"del_patient {selected_indexes}")
            self.item_view_helpers.delete_rows(selected_indexes)
            self.item_view_helpers.save_model_to_db()

    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A patient being double-clicked in the patient view automatically makes
        the session view to update with the data of the patient.
        :param index:
        :return:
        """
        if (index.isValid() and
                hasattr(self.parent, 'upper_layer_model_selected')):
            src_idx = self.proxy_model.mapToSource(index)
            patient_id = self.source_model.get_data_by_index(src_idx, 'patient_id')
            logger.debug(f'patient_id is double-clicked: {patient_id}')
            self.source_model.set_selected_id(patient_id)
            self.parent.upper_layer_model_selected(self.source_model)

    @Slot()
    def emr_id_entered(self):
        emr_id = self.search_bar.text()
        logger.debug(f'emr_id is entered: {emr_id}')
        if (emr_id.isdecimal() and
                hasattr(self.parent, 'upper_layer_model_selected')):
            data = {'patient_emr_id': int(emr_id)}
            patient_id = self.source_model.get_id_by_data(data, 'patient_id')
            if patient_id is not None:
                logger.debug(f'patient_id is selected: {patient_id}')
                self.source_model.set_selected_id(patient_id)
                self.parent.upper_layer_model_selected(self.source_model)
            else:
                self.new_patient_dlg.start_with_emr_id(emr_id)
                self.new_patient_dlg.show()

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        self.source_model.del_new_rows()
        self.source_model.set_selected_id(None)
        self.parent.update_all_signal.emit()
