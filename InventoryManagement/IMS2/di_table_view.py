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
        self._setup_delegate_for_columns()

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

    @abstractmethod
    def _setup_delegate_for_columns(self):
        """
        Needs to be implemented
        :return:
        """

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

    def add_new_row(self):
        """
        Common
        This is called from a Button
        :return:
        """
        new_item_index = self.source_model.add_new_row()
        if new_item_index is None:
            logger.debug(f'add_new_row: Failed creating a new row')
            self.parent.statusBar().showMessage('Failed creating a new row')
        else:
            logger.debug(f'add_new_row: a new row is being created')
            self.parent.statusBar().showMessage('A new row being created')
        return new_item_index

    def change_rows_by_delegate(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'changed' in flag column and allowing the user
        to modify the items
        :param indexes:
        :return:
        """
        chg_rows = set()
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                src_idx = self.proxy_model.mapToSource(idx)
                self.source_model.set_chg_flag(src_idx)
                chg_rows.add(src_idx.row())

        logger.debug(f'change_rows_by_delegate: rows {chg_rows} being changed')

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
