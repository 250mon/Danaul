from typing import List, Dict
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QGroupBox, QMessageBox, QWidget, QTreeView
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from common.d_logger import Logs
from model.patient_model import PatientModel
from ui.di_table_widget import CommonView
from ui.register_new_patient_dialog import NewPatientDialog


logger = Logs().get_logger("main")


class PatientWidget(CommonView):
    def __init__(self, model: PatientModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.source_model = model
        self.initUi()
        self.new_patient_dlg = NewPatientDialog(self)

    def initUi(self):
        self.proxy_model = QSortFilterProxyModel()
        self._setup_proxy_model()

        self.patient_view = QTreeView()
        self.patient_view.setRootIsDecorated(False)
        self.patient_view.setAlternatingRowColors(True)
        self.patient_view.setModel(self.proxy_model)
        self.patient_view.setSortingEnabled(True)

        title_label = QLabel('환자')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)
        refresh_btn = QPushButton('전체새로고침')
        refresh_btn.clicked.connect(self.update_all_views)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.stretch(1)
        hbox1.addWidget(refresh_btn)

        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText('검색어')
        search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        add_btn = QPushButton('신환')
        add_btn.clicked.connect(self.add_patient)
        del_btn = QPushButton('삭제')
        del_btn.clicked.connect(self.del_patient)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(add_btn)
        edit_hbox.addWidget(del_btn)
        edit_hbox.addWidget(save_btn)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_bar)
        hbox2.addStretch(1)
        hbox2.addWidget(edit_hbox)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.patient_view)
        self.setLayout(vbox)

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('patient_emr_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    @Slot()
    def add_patient(self):
        logger.debug("Adding a patient ...")
        self.new_patient_dlg.show()

    @Slot()
    def del_patient(self):
        logger.debug("Deleting patient ...")
        if selected_indexes := self._get_selected_indexes():
            logger.debug(f"del_patient {selected_indexes}")
            self.delete_rows(selected_indexes)

    @Slot()
    def chg_patient(self):
            logger.debug("Changing patient ...")
            if selected_indexes := self._get_selected_indexes():
                logger.debug(f"chg_patient {selected_indexes}")

    @Slot(object)
    def save_model_to_db(self, input_db_record: Dict):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        self.source_model.make_a_new_row_df(**input_db_record)
        if hasattr(self.parent, "async_start"):
            self.parent.async_start("patient_save")

    def _get_selected_indexes(self):
        """
        Common
        :return:
        """
        # the indexes of proxy model
        selected_indexes = self.patient_view.selectedIndexes()
        is_valid_indexes = []
        rows = []
        for idx in selected_indexes:
            is_valid_indexes.append(idx.isValid())
            rows.append(idx.row())

        if len(selected_indexes) > 0 and False not in is_valid_indexes:
            logger.debug(f"Indexes selected: {rows}")
            return selected_indexes
        else:
            logger.debug(f"Indexes not selected or invalid: {selected_indexes}")
            return None

    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A patient being double clicked in the patient view automatically makes
        the session view to update with the data of the patient.
        :param index:
        :return:
        """
        if index.isValid() and hasattr(self.parent, 'patient_selected'):
            patient_id = index.siblingAtColumn(self.source_model.get_col_number('patient_id')).data()
            self.parent.patient_selected(patient_id)

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        self.parent.update_all_signal.emit()
