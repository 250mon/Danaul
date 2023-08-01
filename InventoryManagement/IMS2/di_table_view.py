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
from combobox_delegate import ComboBoxDelegate


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
    @Slot(str, pd.DataFrame)
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
        flag_col = self.source_model.get_col_number('flag')
        for idx in indexes:
            src_idx = self.proxy_model.mapToSource(idx)
            if idx.column() == flag_col:
                self.source_model.set_chg_flag(src_idx)
                logger.debug(f'change_rows_by_delegate: items {src_idx.row()} changed')

    def delete_rows(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        """
        flag_col = self.source_model.get_col_number('flag')
        for idx in indexes:
            src_idx = self.proxy_model.mapToSource(idx)
            if idx.column() == flag_col:
                self.source_model.set_del_flag(src_idx)
                logger.debug(f'delete_rows: rows {src_idx.row()} deleted')

    async def save_to_db(self):
        """
        Common
        :return:
        """
        result_str = await self.source_model.update_db()
        if result_str is not None:
            QMessageBox.information(self,
                                    'Save Results',
                                    result_str,
                                    QMessageBox.Close)
        # update model_df
        logger.debug('Updating model_df ...')
        await self.source_model.update_model_df_from_db()

        return result_str

