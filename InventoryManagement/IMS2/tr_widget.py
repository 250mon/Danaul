import os
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from di_logger import Logs, logging
from di_table_view import InventoryTableView
from single_tr_window import SingleTrWindow


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class TrWidget(InventoryTableView):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # Filtering is performed on item_name column
        search_col_num = self.source_model.get_col_number('tr_type')
        self.proxy_model.setFilterKeyColumn(search_col_num)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('tr_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_table_view(self):
        super()._setup_table_view()
        self.table_view.doubleClicked.connect(self.row_double_clicked)
        self.table_view.activated.connect(self.row_activated)

    def setup_delegate_for_columns(self):
        """
        :return:
        """
        super().setup_delegate_for_columns()


    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText('매입/매출 입력')
        search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        buy_btn = QPushButton('매입')
        buy_btn.clicked.connect(lambda: self.do_actions("buy"))
        sell_btn = QPushButton('매출')
        sell_btn.clicked.connect(lambda: self.do_actions("sell"))
        adj_plus_btn = QPushButton('조정+')
        adj_plus_btn.clicked.connect(lambda: self.do_actions("adj+"))
        adj_minus_btn = QPushButton('조정-')
        adj_minus_btn.clicked.connect(lambda: self.do_actions("adj-"))
        save_sku_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_sku_btn.clicked.connect(lambda: self.parent.async_start("tr_save"))
        sku_hbox = QHBoxLayout()
        sku_hbox.addWidget(search_bar)
        sku_hbox.addStretch(1)
        sku_hbox.addWidget(buy_btn)
        sku_hbox.addWidget(sell_btn)
        sku_hbox.addWidget(adj_plus_btn)
        sku_hbox.addWidget(adj_minus_btn)
        sku_hbox.addWidget(save_sku_btn)
        sku_vbox = QVBoxLayout()
        sku_vbox.addLayout(sku_hbox)
        sku_vbox.addWidget(self.table_view)
        self.setLayout(sku_vbox)

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        logger.debug(f'do_action: {action}')
        if action == "buy":
            logger.debug('buying ...')
            self.add_new_row('buy')

        elif action == "sell":
            logger.debug('selling ...')
            if selected_indexes := self._get_selected_indexes():
                self.change_rows_by_delegate(selected_indexes)

        elif action == "del_sku":
            logger.debug('Deleting sku ...')
            if selected_indexes := self._get_selected_indexes():
                self.delete_rows(selected_indexes)


    def add_new_row(self, type: str):
        self.source_model.append_new_row()

    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        An item being double clicked in item view automatically makes
        the sku view to do filtering to show the skus of the item only.
        :param index:
        :return:
        """
        if index.isValid():
            src_idx = self.proxy_model.mapToSource(index)
            sku_id = int(src_idx.siblingAtColumn(0).data())
            if hasattr(self.parent, 'sku_selected'):
                self.parent.sku_selected(sku_id)

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

    def filter_selected_item(self, item_id: int):
        """
        A double-click event in item.table_view triggers the parent's
        item_selected method which in turn calls this method
        :param item_id:
        :return:
        """
        self.proxy_model.setFilterRegularExpression(f"^{item_id}$")
        # self.proxy_model.setFilterFixedString(item_id)
