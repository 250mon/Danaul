import os
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QDate
from PySide6.QtGui import QFont
from di_logger import Logs, logging
from di_lab import Lab
from di_table_widget import InventoryTableWidget
from tr_model import TrModel
from single_tr_window import SingleTrWindow
from constants import ADMIN_GROUP, UserPrivilege


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class TrWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def set_source_model(self, model: TrModel):
        self.source_model = model
        self._apply_model()

    def set_source_model(self, model: TrModel):
        """
        Override method for using tr_model's methods (validate_new_row)
        :param model:
        :return:
        """
        super().set_source_model(model)

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # Filtering is performed on item_name column
        search_col_num = self.source_model.get_col_number('sku_id')
        self.proxy_model.setFilterKeyColumn(search_col_num)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('tr_id')

        # descending order makes problem with mapToSource index
        # self.proxy_model.sort(initial_sort_col_num, Qt.DescendingOrder)
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_initial_table_view(self):
        super()._setup_initial_table_view()
        self.table_view.activated.connect(self.row_activated)

    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        self.set_col_hidden('tr_type_id')
        # Unlike item_widget and sku_widget, tr_widget always allows editing
        # because there is no select mode
        self.source_model.set_editable(True)

        title_label = QLabel('거래내역')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.stretch(1)

        # search_bar = QLineEdit(self)
        # search_bar.setPlaceholderText('매입/매출 입력')
        # search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        search_all_btn = QPushButton('전체조회')
        search_all_btn.clicked.connect(self.filter_no_selection)
        beg_dateedit = QDateEdit()
        beg_dateedit.setDate(self.source_model.beg_timestamp)
        beg_dateedit.dateChanged.connect(self.source_model.set_beg_timestamp)
        end_dateedit = QDateEdit()
        end_dateedit.setDate(self.source_model.end_timestamp)
        end_dateedit.dateChanged.connect(self.source_model.set_end_timestamp)
        date_search_btn = QPushButton('조회')
        date_search_btn.clicked.connect(lambda: self.filter_selection(
            self.source_model.selected_upper_id))
        two_search_btn = QPushButton('2')
        two_search_btn.clicked.connect(lambda: self.set_max_search_count(2))
        five_search_btn = QPushButton('5')
        five_search_btn.clicked.connect(lambda: self.set_max_search_count(5))
        ten_search_btn = QPushButton('10')
        ten_search_btn.clicked.connect(lambda: self.set_max_search_count(10))
        twenty_search_btn = QPushButton('20')
        twenty_search_btn.clicked.connect(lambda: self.set_max_search_count(20))

        self.sku_name_label = QLabel()
        font = QFont("Arial", 14, QFont.Bold)
        self.sku_name_label.setFont(font)

        buy_btn = QPushButton('매입')
        buy_btn.clicked.connect(lambda: self.do_actions("buy"))
        sell_btn = QPushButton('매출')
        sell_btn.clicked.connect(lambda: self.do_actions("sell"))
        adj_plus_btn = QPushButton('조정+')
        adj_plus_btn.clicked.connect(lambda: self.do_actions("adj+"))
        adj_minus_btn = QPushButton('조정-')
        adj_minus_btn.clicked.connect(lambda: self.do_actions("adj-"))
        save_btn = QPushButton('저장')
        save_btn.clicked.connect(self.save_model_to_db)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_all_btn)
        hbox2.addWidget(beg_dateedit)
        hbox2.addWidget(end_dateedit)
        hbox2.addWidget(date_search_btn)
        hbox2.addWidget(two_search_btn)
        hbox2.addWidget(five_search_btn)
        hbox2.addWidget(ten_search_btn)
        hbox2.addWidget(twenty_search_btn)
        hbox2.addStretch(1)

        hbox2.addWidget(self.sku_name_label)
        hbox2.addStretch(1)
        hbox2.addWidget(buy_btn)
        hbox2.addWidget(sell_btn)
        hbox2.addWidget(adj_plus_btn)
        hbox2.addWidget(adj_minus_btn)
        hbox2.addWidget(save_btn)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.table_view)

        if self.source_model.get_user_privilege() == UserPrivilege.Admin:
            del_tr_btn = QPushButton('관리자 삭제/해제')
            del_tr_btn.clicked.connect(lambda: self.do_actions("del_tr"))
            del_hbox = QHBoxLayout()
            del_hbox.addStretch(1)
            del_hbox.addWidget(del_tr_btn)
            vbox.addLayout(del_hbox)

        self.setLayout(vbox)

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        logger.debug(f"{action}")

        if action == "buy":
            logger.debug("buying ...")
            self.add_new_tr('Buy')
        elif action == "sell":
            logger.debug("selling ...")
            self.add_new_tr('Sell')
        elif action == "adj+":
            logger.debug("adjusting plus ...")
            self.add_new_tr(tr_type='AdjustmentPlus')
        elif action == "adj-":
            logger.debug("adjusting minus ...")
            self.add_new_tr(tr_type='AdjustmentMinus')
        elif action == "del_tr":
            logger.debug("Deleting tr ...")
            if selected_indexes := self._get_selected_indexes():
                self.delete_rows(selected_indexes)

    def save_model_to_db(self):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        self.source_model.update_sku_qty()

        if hasattr(self.parent, "async_start"):
            self.parent.async_start("tr_save")

    def add_new_tr(self, tr_type) -> bool:
        if self.add_new_row(tr_type=tr_type):
            self.tr_window = SingleTrWindow(self.proxy_model, self)
            return True
        else:
            QMessageBox.information(self,
                                    "Failed New Sku",
                                    "세부품목을 먼저 선택하세요.",
                                    QMessageBox.Close)
            return False

    @Slot(object)
    def added_new_tr_by_single_tr_window(self, index: QModelIndex):
        """
        This is called when SingleTrWindow emits a signal
        It validates the newly added item(the last index)
        If it fails to pass the validation, remove it.
        :return:
        """
        logger.debug(f"tr {index.row()} added")

        src_idx = self.proxy_model.mapToSource(index)
        if not self.source_model.validate_new_row(src_idx):
            self.source_model.drop_rows([src_idx])

    @Slot(QModelIndex)
    def row_activated(self, index: QModelIndex):
        """
        While changing items, activating other items would make changing
        to stop.
        :param index:
        :return:
        """
        src_idx = self.proxy_model.mapToSource(index)
        if src_idx.row() not in self.source_model.editable_rows_set:
            self.source_model.clear_editable_rows()

    def update_tr_view(self):
        # if there is remaining unsaved new rows, drop them
        self.source_model.del_new_rows()
        # retrieve the data about the selected sku_id from DB
        self.parent.async_start('tr_update')
        # displaying the sku name in the tr view
        self.sku_name_label.setText(self.source_model.selected_upper_name)

    def filter_selection(self, sku_id: int):
        """
        A double-click event in the sku view triggers the parent's
        sku_selected method which in turn calls this method
        :param sku_id:
        :return:
        """
        logger.debug(f"sku_id({sku_id})")
        # set selected_sku_id
        self.source_model.set_upper_model_id(sku_id)
        self.update_tr_view()

    def filter_no_selection(self):
        """
        Connected to search all button
        :return:
        """
        # set selected_sku_id to None
        self.source_model.set_upper_model_id(None)
        self.update_tr_view()

    def set_max_search_count(self, max_count: int):
        Lab().set_max_transaction_count(max_count)
        self.filter_selection(self.source_model.selected_upper_id)
