from typing import Dict
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QMessageBox, QDateEdit, QWidget, QTableView
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from db.ds_lab import Lab
from model.session_model import SessionModel
from ui.item_view_helpers import ItemViewHelpers
from ui.single_session_window import SingleSessionWindow
from ui.register_new_session_dialog import NewSessionDialog
from constants import UserPrivilege
from common.d_logger import Logs


logger = Logs().get_logger("main")


class SessionWidget(QWidget):
    def __init__(self, model: SessionModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.source_model = model
        # initialize
        self.set_model()
        self.init_ui()

    def set_model(self):
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('session_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def init_ui(self):
        self.session_view = QTableView()
        self.item_view_helpers = ItemViewHelpers(
            self.source_model,
            self.proxy_model,
            self.session_view)
        self.session_view.setModel(self.proxy_model)
        # self.single_session_window = SingleSessionWindow(self.proxy_model, self)
        self.new_session_dlg = NewSessionDialog(self)

        self.session_view.setAlternatingRowColors(True)
        self.session_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.session_view.resizeColumnsToContents()
        self.session_view.setSortingEnabled(True)

        self.item_view_helpers.set_col_hidden("session_id")
        self.item_view_helpers.set_col_hidden('patient_id')
        self.item_view_helpers.set_col_hidden("provider_id")
        self.item_view_helpers.set_col_hidden("modality_id")
        self.item_view_helpers.set_col_hidden("part_id")
        self.item_view_helpers.set_col_hidden("user_id")
        self.item_view_helpers.set_col_width("patient_name", 50)
        self.item_view_helpers.set_col_width("provider_name", 50)
        self.item_view_helpers.set_col_width("modality_name", 50)
        self.item_view_helpers.set_col_width("part_name", 50)
        self.item_view_helpers.set_col_width("timestamp", 200)
        self.item_view_helpers.set_col_width("description", 600)
        # Unlike treatment_widget and sku_widget, tr_widget always allows editing
        # because there is no select mode
        self.source_model.set_editable(True)

        title_label = QLabel('치료 세션')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)

        beg_dateedit = QDateEdit()
        # beg_dateedit.setMaximumWidth(100)
        beg_dateedit.setDate(self.source_model.beg_timestamp)
        beg_dateedit.dateChanged.connect(self.source_model.set_beg_timestamp)
        end_dateedit = QDateEdit()
        # end_dateedit.setMaximumWidth(100)
        end_dateedit.setDate(self.source_model.end_timestamp)
        end_dateedit.dateChanged.connect(self.source_model.set_end_timestamp)
        date_search_btn = QPushButton('조회')
        # date_search_btn.setMaximumWidth(100)
        date_search_btn.clicked.connect(lambda: self.filter_for_selected_id(
            self.source_model.selected_patient_id))

        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.addWidget(beg_dateedit)
        hbox1.addWidget(end_dateedit)
        hbox1.addWidget(date_search_btn)
        hbox1.addStretch(1)

        search_all_btn = QPushButton('전체조회')
        search_all_btn.clicked.connect(self.filter_for_search_all)
        two_search_btn = QPushButton('2')
        two_search_btn.clicked.connect(lambda: self.set_max_search_count(2))
        five_search_btn = QPushButton('5')
        five_search_btn.clicked.connect(lambda: self.set_max_search_count(5))
        ten_search_btn = QPushButton('10')
        ten_search_btn.clicked.connect(lambda: self.set_max_search_count(10))
        twenty_search_btn = QPushButton('20')
        twenty_search_btn.clicked.connect(lambda: self.set_max_search_count(20))

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_all_btn)
        hbox2.addWidget(two_search_btn)
        hbox2.addWidget(five_search_btn)
        hbox2.addWidget(ten_search_btn)
        hbox2.addWidget(twenty_search_btn)
        hbox2.addStretch(1)

        self.patient_name_label = QLabel()
        font = QFont("Arial", 14, QFont.Bold)
        self.patient_name_label.setFont(font)
        hbox2.addWidget(self.patient_name_label)

        new_btn = QPushButton('추가')
        new_btn.clicked.connect(self.add_session)
        chg_btn = QPushButton('변경')
        chg_btn.clicked.connect(self.chg_session)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(new_btn)
        edit_hbox.addWidget(chg_btn)
        hbox2.addLayout(edit_hbox)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.session_view)

        if self.source_model.get_user_privilege() == UserPrivilege.Admin:
            del_tr_btn = QPushButton('관리자 삭제/해제')
            del_tr_btn.clicked.connect(self.del_session)
            del_hbox = QHBoxLayout()
            del_hbox.addStretch(1)
            del_hbox.addWidget(del_tr_btn)
            vbox.addLayout(del_hbox)

        self.setLayout(vbox)

    @Slot(str)
    def add_session(self):
        logger.debug("Adding a new session ...")
        self.new_session_dlg.set_source_model(self.source_model)
        self.new_session_dlg.show()

    @Slot(str)
    def chg_session(self):
        logger.debug("Changing a session...")
        if selected_indexes := self.item_view_helpers.get_selected_indexes():
            self.item_view_helpers.change_rows(selected_indexes)

    @Slot(str)
    def del_session(self):
        logger.debug("Admin deleting a session ...")
        if selected_indexes := self.item_view_helpers.get_selected_indexes():
            self.item_view_helpers.delete_rows(selected_indexes)

    @Slot(object)
    def save_model_to_db(self, input_db_record: Dict):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        try:
            self.source_model.append_new_row(**input_db_record)
            if hasattr(self.parent, "async_start"):
                self.parent.async_start("session_save")
        except Exception as e:
            QMessageBox.information(self,
                                    "Failed New Session",
                                    str(e),
                                    QMessageBox.Close)

    @Slot(QModelIndex)
    def row_activated(self, index: QModelIndex):
        """
        While changing sessions, selecting other sessions would make changing
        to stop.
        :param index:
        :return:
        """
        src_idx = self.prx_model.mapToSource(index)
        if src_idx.row() not in self.source_model.editable_rows_set:
            self.source_model.clear_editable_rows()

    def update_session_view(self):
        # retrieve the data about the selected treatment_id from DB
        self.parent.async_start('session_update')
        # displaying the sku name in the tr view
        self.patient_name_label.setText(self.source_model.selected_patient_name)

    def filter_for_selected_id(self, patient_id: int):
        """
        A double-click event in the patient view triggers the parent's
        patient_selected method which in turn calls this method
        :param patient_id:
        :return:
        """
        logger.debug(f"patient_id({patient_id})")
        # if there is remaining unsaved new rows, drop them
        self.source_model.del_new_rows()
        # set selected_treatment_id
        self.source_model.set_upper_model_id(patient_id)
        self.update_session_view()

    def filter_for_search_all(self):
        """
        Connected to search all button
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        self.source_model.del_new_rows()
        # set selected_patient_id to None
        self.source_model.set_upper_model_id(None)
        self.update_session_view()

    def set_max_search_count(self, max_count: int):
        Lab()._set_max_session_count(max_count)
        self.filter_for_selected_id(self.source_model.selected_patient_id)
