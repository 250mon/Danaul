import os
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QMessageBox
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QFont
from di_logger import Logs, logging
from di_table_widget import InventoryTableWidget
from tr_model import TrModel
from single_tr_window import SingleTrWindow
from constants import ADMIN_GROUP


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class TrWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def set_source_model(self, model: TrModel):
        """
        Common
        :param model:
        :return:
        """
        self.source_model = model
        self._apply_model()

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
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_initial_table_view(self):
        super()._setup_initial_table_view()
        self.table_view.activated.connect(self.row_activated)

    def _setup_delegate_for_columns(self):
        """
        :return:
        """
        super()._setup_delegate_for_columns()

    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        self.set_col_hidden('tr_type_id')

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

        self.sku_name_label = QLabel()
        font = QFont("Arial", 12, QFont.Bold)
        self.sku_name_label.setFont(font)

        buy_btn = QPushButton('매입')
        buy_btn.clicked.connect(lambda: self.do_actions("buy"))
        sell_btn = QPushButton('매출')
        sell_btn.clicked.connect(lambda: self.do_actions("sell"))
        adj_plus_btn = QPushButton('조정+')
        adj_plus_btn.clicked.connect(lambda: self.do_actions("adj+"))
        adj_minus_btn = QPushButton('조정-')
        adj_minus_btn.clicked.connect(lambda: self.do_actions("adj-"))
        save_tr_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_tr_btn.clicked.connect(lambda: self.parent.async_start("tr_save"))
        del_tr_btn = QPushButton('관리자 삭제/해제')
        del_tr_btn.clicked.connect(lambda: self.do_actions("del_tr"))
        if self.source_model.user_name not in ADMIN_GROUP:
            del_tr_btn.setEnabled(False)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_all_btn)
        hbox2.addStretch(1)
        hbox2.addWidget(self.sku_name_label)
        hbox2.addStretch(1)
        hbox2.addWidget(buy_btn)
        hbox2.addWidget(sell_btn)
        hbox2.addWidget(adj_plus_btn)
        hbox2.addWidget(adj_minus_btn)
        hbox2.addWidget(save_tr_btn)

        del_hbox = QHBoxLayout()
        del_hbox.addStretch(1)
        del_hbox.addWidget(del_tr_btn)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.table_view)
        vbox.addLayout(del_hbox)

        self.setLayout(vbox)

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        logger.debug(f'do_action: {action}')

        if action == "buy":
            logger.debug('do_actions: buying ...')
            self.add_new_tr('Buy')
        elif action == "sell":
            logger.debug('do_actions: selling ...')
            self.add_new_tr('Sell')
        elif action == "adj+":
            logger.debug('do_actions: adjusting plus ...')
            self.add_new_tr(tr_type='AdjustmentPlus')
        elif action == "adj-":
            logger.debug('do_actions: adjusting minus ...')
            self.add_new_tr(tr_type='AdjustmentMinus')
        elif action == "del_tr":
            logger.debug('Deleting tr ...')
            if selected_indexes := self._get_selected_indexes():
                self.delete_rows(selected_indexes)

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
        logger.debug(f'added_new_tr_by_single_tr_window: tr {index.row()} added')

        if not self.source_model.validate_new_row(index):
            self.source_model.drop_rows([index])

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

    def filter_selection(self, sku_index: QModelIndex):
        """
        A double-click event in the sku view triggers the parent's
        sku_selected method which in turn calls this method
        :param sku_id:
        :return:
        """
        super().filter_selection(sku_index)
        # displaying the sku name in the tr view
        self.sku_name_label.setText(self.source_model.selected_upper_name)

    def filter_no_selection(self):
        """
        Connected to search all button
        :return:
        """
        super().filter_no_selection()
        # displaying the sku name in the tr view
        self.sku_name_label.setText("")
