from typing import Dict
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QMessageBox, QDateEdit, QWidget, QTableView, QGroupBox
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from common.async_helper import AsyncHelper
from common.d_logger import Logs
from db.ds_lab import Lab
from model.di_data_model import DataModel
from model.patient_model import PatientModel
from model.session_model import SessionModel
from ui.item_view_helpers import ItemViewHelpers
from ui.register_new_session_dialog import NewSessionDialog


logger = Logs().get_logger("main")


class SessionWidget(QWidget):
    def __init__(self, model: SessionModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.async_helper: AsyncHelper = self.parent.async_helper
        self.source_model = model
        self.proxy_model = None
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
        self.item_view_helpers = ItemViewHelpers(self.source_model,
                                                 self.proxy_model,
                                                 self.session_view,
                                                 self)
        self.session_view.setModel(self.proxy_model)

        self.session_view.setAlternatingRowColors(True)
        self.session_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.session_view.resizeColumnsToContents()
        self.session_view.setSortingEnabled(True)

        self.new_session_dlg = NewSessionDialog(self.source_model, self)
        self.new_session_dlg.new_session_signal.connect(self.item_view_helpers.save_model_to_db)

        self.item_view_helpers.set_col_width("patient_emr_id", 70)
        self.item_view_helpers.set_col_width("patient_name", 70)
        self.item_view_helpers.set_col_width("provider_name", 70)
        self.item_view_helpers.set_col_width("modality_name", 100)
        self.item_view_helpers.set_col_width("part_name", 100)
        self.item_view_helpers.set_col_width("timestamp", 100)
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
        date_search_btn.clicked.connect(lambda: self.set_max_search_count(20))

        search_all_btn = QPushButton('전체조회')
        search_all_btn.clicked.connect(lambda: self.update_with_no_selection(None))
        two_search_btn = QPushButton('2')
        two_search_btn.clicked.connect(lambda: self.set_max_search_count(2))
        five_search_btn = QPushButton('5')
        five_search_btn.clicked.connect(lambda: self.set_max_search_count(5))
        ten_search_btn = QPushButton('10')
        ten_search_btn.clicked.connect(lambda: self.set_max_search_count(10))
        twenty_search_btn = QPushButton('20')
        twenty_search_btn.clicked.connect(lambda: self.set_max_search_count(20))

        self.filter_item_label = QLabel()
        font = QFont("Arial", 14, QFont.Bold)
        self.filter_item_label.setFont(font)

        new_btn = QPushButton('추가')
        new_btn.clicked.connect(self.add_session)
        chg_btn = QPushButton('수정 저장')
        chg_btn.clicked.connect(self.chg_session)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(new_btn)
        edit_hbox.addWidget(chg_btn)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.addWidget(beg_dateedit)
        hbox1.addWidget(end_dateedit)
        hbox1.addWidget(date_search_btn)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_all_btn)
        hbox2.addWidget(two_search_btn)
        hbox2.addWidget(five_search_btn)
        hbox2.addWidget(ten_search_btn)
        hbox2.addWidget(twenty_search_btn)
        hbox1.addStretch(1)
        hbox2.addWidget(self.filter_item_label)
        hbox2.addStretch(1)
        hbox2.addLayout(edit_hbox)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.session_view)

        del_tr_btn = QPushButton('관리자 삭제/해제')
        del_tr_btn.clicked.connect(self.del_session)
        del_hbox = QHBoxLayout()
        del_hbox.addStretch(1)
        del_hbox.addWidget(del_tr_btn)
        self.admin_menu_grp = QGroupBox(self)
        self.admin_menu_grp.setLayout(del_hbox)
        vbox.addWidget(self.admin_menu_grp)

        self.setLayout(vbox)

    def set_admin_menu_enabled(self, val: bool):
        self.admin_menu_grp.setEnabled(val)

    @Slot(str)
    def add_session(self):
        if not isinstance(self.source_model.upper_model, PatientModel):
            logger.debug("Cannot add a new session: choose a patient first")
        else:
            logger.debug("Adding a new session ...")
            self.new_session_dlg.update_with_latest_model()
            self.new_session_dlg.show()

    @Slot(str)
    def chg_session(self):
        logger.debug("Saving changed sessions...")
        self.item_view_helpers.save_model_to_db()

    @Slot(str)
    def del_session(self):
        logger.debug("Admin deleting a session ...")
        if selected_indexes := self.item_view_helpers.get_selected_indexes():
            self.item_view_helpers.delete_rows(selected_indexes)
            self.item_view_helpers.save_model_to_db()

    @Slot(QModelIndex)
    def row_activated(self, index: QModelIndex):
        """
        While changing sessions, selecting other sessions would make changing
        to stop.
        :param index:
        :return:
        """
        src_idx = self.proxy_model.mapToSource(index)
        if src_idx.row() not in self.source_model.editable_rows_set:
            self.source_model.clear_editable_rows()

    def update_with_selected_upper_layer(self, upper_model: DataModel):
        """
        A double click event on a row of the upper level widget eventually
         calls this method
        :param upper_model
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        try:
            self.source_model.del_new_rows()
        except Exception as e:
            logger.exception(e)

        # let the model learn the upper model index for a new row creation
        self.source_model.set_upper_model(upper_model)
        self.update_view()

    def set_max_search_count(self, max_count: int):
        Lab().set_max_session_count(max_count)
        self.update_view()

    def update_view(self):
        # retrieve the data about the selected patient_id from DB
        self.parent.async_start('session_update')

        # displaying the selected item name in the session view
        self.filter_item_label.setText(self.source_model.selected_model_name + ": " +
                                       self.source_model.selected_name)
