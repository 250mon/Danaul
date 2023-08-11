import os
from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from di_logger import Logs, logging
from di_table_widget import InventoryTableWidget
from item_model import ItemModel
from single_item_window import SingleItemWindow

logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class ItemWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.delegate_mode = True

    def set_source_model(self, model: ItemModel):
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
        # search_col_num = self.source_model.get_col_number('item_name')
        # self.proxy_model.setFilterKeyColumn(search_col_num)

        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('item_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_initial_table_view(self):
        """
        Carried out before the model is set to the table view
        :return:
        """
        super()._setup_initial_table_view()
        self.table_view.doubleClicked.connect(self.row_double_clicked)
        self.table_view.activated.connect(self.row_activated)

    def _setup_delegate_for_columns(self):
        super()._setup_delegate_for_columns()

    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        self.set_col_hidden('category_id')

        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText('검색어')
        search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        add_item_btn.clicked.connect(lambda: self.do_actions("add_item"))
        chg_item_btn = QPushButton('수정')
        chg_item_btn.clicked.connect(lambda: self.do_actions("chg_item"))
        del_item_btn = QPushButton('삭제/해제')
        del_item_btn.clicked.connect(lambda: self.do_actions("del_item"))
        save_item_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_item_btn.clicked.connect(lambda: self.parent.async_start("item_save"))
        item_hbox = QHBoxLayout()
        item_hbox.addWidget(search_bar)
        item_hbox.addStretch(1)
        item_hbox.addWidget(add_item_btn)
        item_hbox.addWidget(chg_item_btn)
        item_hbox.addWidget(del_item_btn)
        item_hbox.addWidget(save_item_btn)
        item_vbox = QVBoxLayout()
        item_vbox.addLayout(item_hbox)
        item_vbox.addWidget(self.table_view)
        self.setLayout(item_vbox)

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        logger.debug(f'do_action: {action}')
        if action == "add_item":
            logger.debug('Adding item ...')
            self.add_new_row()
            if not self.delegate_mode:
                # Input window mode using DataMapperWidget
                new_item_index = self.source_model.index(self.source_model.rowCount()-1, 0)
                self.item_window = SingleItemWindow(self.proxy_model,
                                                    new_item_index, self)

        elif action == "chg_item":
            logger.debug('Changing item ...')
            if selected_indexes := self._get_selected_indexes():
                logger.debug(f'do_actions: chg_item {selected_indexes}')
                if self.delegate_mode:
                    self.change_rows_by_delegate(selected_indexes)
                else:
                    self.item_window = SingleItemWindow(self.proxy_model,
                                                        selected_indexes, self)

        elif action == "del_item":
            logger.debug('Deleting item ...')
            if selected_indexes := self._get_selected_indexes():
                logger.debug(f'do_actions: del_item {selected_indexes}')
                self.delete_rows(selected_indexes)

    @Slot(object)
    def added_new_item_by_single_item_window(self, index: QModelIndex):
        """
        This is called when SingleItemWindow emits a signal
        It validates the newly added item. If it fails, remove it.
        index is indicating the item_id column of a new item
        :return:
        """
        if self.source_model.is_flag_column(index):
            logger.debug(f'added_new_item_by_single_item_window: item {index.row()} added')

        if not self.source_model.validate_new_row(index):
            self.source_model.drop_rows([index])

    @Slot(object)
    def changed_items_by_single_item_window(self, indexes: List[QModelIndex]):
        """
        This is called when SingleItemWindow emits a signal
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                self.source_model.set_chg_flag(idx)
                logger.debug(f'changed_items_by_single_item_window: items {idx.row()} changed')


    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        An item being double clicked in the item view automatically makes
        the sku view to do filtering to show the skus of the selected item.
        :param index:
        :return:
        """
        if index.isValid():
            src_idx = self.proxy_model.mapToSource(index)
            if hasattr(self.parent, 'item_selected'):
                self.parent.item_selected(src_idx)

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
            self.rows = self.source_model.clear_editable_rows()
