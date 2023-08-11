import os
import pandas as pd
from typing import List
from abc import abstractmethod
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QPushButton, QLineEdit,
    QTableView, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QSortFilterProxyModel, QModelIndex
)
from di_data_model import DataModel
from di_default_delegate import DefaultDelegate
from combobox_delegate import ComboBoxDelegate
from spinbox_delegate import SpinBoxDelegate
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class InventoryTableView(QWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def set_source_model(self, model: DataModel):
        """
        Common
        :param model:
        :return:
        """
        self.source_model = model
        self._apply_model()

    def _apply_model(self):
        """
        Common
        :return:
        """
        # QSortFilterProxyModel enables filtering columns and sorting rows
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self._setup_proxy_model()

        self._setup_table_view()
        self.table_view.setModel(self.proxy_model)
        self.setup_delegate_for_columns()

        self._setup_ui()

    @abstractmethod
    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """

    def _setup_table_view(self):
        """
        Common
        :return:
        """
        # table view
        self.table_view = QTableView(self)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.resizeColumnsToContents()
        self.table_view.setSortingEnabled(True)
        self.setStyleSheet(
            "QTableView::item:selected"
            "{"
            "background-color : #d9fffb;"
            "selection-color : #000000;"
            "}"
        )

    def setup_delegate_for_columns(self):
        """
        Sets up appropriate delegates for columns
        :return:
        """
        for col_idx in self.source_model.get_default_delegate_info():
            default_delegate = DefaultDelegate(self)
            default_delegate.set_model(self.source_model)
            self.table_view.setItemDelegateForColumn(col_idx, default_delegate)

        for col_idx, val_list in self.source_model.get_combobox_delegate_info().items():
            combo_delegate = ComboBoxDelegate(val_list, self)
            combo_delegate.set_model(self.source_model)
            self.table_view.setItemDelegateForColumn(col_idx, combo_delegate)

        for col_idx, val_list in self.source_model.get_spinbox_delegate_info().items():
            spin_delegate = SpinBoxDelegate(*val_list, self)
            spin_delegate.set_model(self.source_model)
            self.table_view.setItemDelegateForColumn(col_idx, spin_delegate)

    @abstractmethod
    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """

    def _get_selected_indexes(self):
        """
        Common
        :return:
        """
        # the indexes of proxy model
        selected_indexes = self.table_view.selectedIndexes()
        check_indexes = [idx.isValid() for idx in selected_indexes]
        if len(selected_indexes) > 0 and False not in check_indexes:
            logger.debug(f'Indexes selected: {selected_indexes}')
            return selected_indexes
        else:
            logger.debug(f'Indexes not selected or invalid: {selected_indexes}')
            return None

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """

    def add_new_row(self, **kwargs):
        """
        Common
        This is called from a Button
        :return:
        """
        self.source_model.append_new_row(**kwargs)

    def change_rows_by_delegate(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'changed' in flag column and allowing the user
        to modify the items
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                src_idx = self.proxy_model.mapToSource(idx)
                self.source_model.set_chg_flag(src_idx)

        logger.debug(f'change_rows_by_delegate: rows {src_idx.row()} being changed')

    def delete_rows(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                src_idx = self.proxy_model.mapToSource(idx)
                self.source_model.set_del_flag(src_idx)
                logger.debug(f'delete_rows: rows {src_idx.row()} deleted')

    async def save_to_db(self):
        """
        Common
        :return:
        """
        result_str = await self.source_model.save_to_db()
        if result_str is not None:
            QMessageBox.information(self,
                                    'Save Results',
                                    result_str,
                                    QMessageBox.Close)
        return result_str

    def filter_selection(self, upper_index: QModelIndex):
        """
        A double-click event in the view triggers the parent's
        item_selected method which in turn calls this method
        :param item_id:
        :return:
        """
        # let sku model learn item model index for new row creation
        self.source_model.set_upper_model_index(upper_index)

        # filtering in the sku view
        self.proxy_model.setFilterRegularExpression(
            f"^{self.source_model.selected_upper_id}$")

    def filter_no_selection(self):
        self.proxy_model.setFilterRegularExpression("^\\d*$")
        self.source_model.set_upper_model_index(None)
