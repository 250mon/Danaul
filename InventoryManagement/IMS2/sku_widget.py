import os
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from di_logger import Logs, logging
from di_table_view import InventoryTableView


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class SkuWidget(InventoryTableView):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # Filtering is performed on item_name column
        search_col_num = self.source_model.get_col_number('item_id')
        self.proxy_model.setFilterKeyColumn(search_col_num)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('sku_id')
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
        # search_bar = QLineEdit(self)
        # search_bar.setPlaceholderText('품목명 입력')
        # search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        view_all_btn = QPushButton('전체조회')
        view_all_btn.clicked.connect(lambda : self.filter_selected_item(None))
        add_sku_btn = QPushButton('추가')
        add_sku_btn.clicked.connect(lambda: self.do_actions("add_sku"))
        chg_sku_btn = QPushButton('수정')
        chg_sku_btn.clicked.connect(lambda: self.do_actions("chg_sku"))
        del_sku_btn = QPushButton('삭제/해제')
        del_sku_btn.clicked.connect(lambda: self.do_actions("del_sku"))
        save_sku_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_sku_btn.clicked.connect(lambda: self.parent.async_start("sku_save"))
        sku_hbox = QHBoxLayout()
        sku_hbox.addWidget(view_all_btn)
        sku_hbox.addStretch(1)
        sku_hbox.addWidget(add_sku_btn)
        sku_hbox.addWidget(chg_sku_btn)
        sku_hbox.addWidget(del_sku_btn)
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
        if action == "add_sku":
            logger.debug('Adding sku ...')
            self.add_new_row()

        elif action == "chg_sku":
            logger.debug('Changing sku ...')
            if selected_indexes := self._get_selected_indexes():
                self.change_rows_by_delegate(selected_indexes)

        elif action == "del_sku":
            logger.debug('Deleting sku ...')
            if selected_indexes := self._get_selected_indexes():
                self.delete_rows(selected_indexes)


    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A sku being double clicked in the sku view automatically makes
        the transaction view to do filtering to show the transactions of
        the selected sku.
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
        While changing rows, activating other rows would make the change
        to stop.
        :param index:
        :return:
        """
        src_idx = self.proxy_model.mapToSource(index)
        if src_idx.row() not in self.source_model.editable_rows_set:
            self.source_model.clear_editable_rows()

    def filter_selected_item(self, item_id: int or None):
        """
        A double-click event in the item view triggers the parent's
        item_selected method which in turn calls this method
        :param item_id:
        :return:
        """
        if item_id is None:
            self.proxy_model.setFilterRegularExpression("^\\d*$")
        else:
            self.proxy_model.setFilterRegularExpression(f"^{item_id}$")
        # self.proxy_model.setFilterFixedString(item_id)
