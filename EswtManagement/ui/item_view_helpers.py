from typing import List
from PySide6.QtWidgets import (
    QWidget, QAbstractItemView, QTableView, QMessageBox
)
from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, Slot
from common.async_helper import AsyncHelper
from common.d_logger import Logs
from model.di_data_model import DataModel
from ui.default_delegate import DefaultDelegate
from ui.combobox_delegate import ComboBoxDelegate
from ui.spinbox_delegate import SpinBoxDelegate

logger = Logs().get_logger("main")


class ItemViewHelpers:
    def __init__(self,
                 src_model: DataModel,
                 proxy_model: QSortFilterProxyModel,
                 view: QAbstractItemView,
                 parent: QWidget = None):
        self.parent: QWidget = parent
        self.async_helper: AsyncHelper = self.parent.async_helper
        self.src_model = src_model
        self.prx_model = proxy_model
        self.item_view: QAbstractItemView = view
        self.setup_delegate_for_columns()

    def setup_delegate_for_columns(self):
        """
        Sets up appropriate delegates for columns
        :return:
        """
        for col_idx in self.src_model.get_default_delegate_info():
            default_delegate = DefaultDelegate(self.item_view)
            default_delegate.set_model(self.src_model)
            self.item_view.setItemDelegateForColumn(col_idx, default_delegate)

        for col_idx, val_list in self.src_model.get_combobox_delegate_info().items():
            combo_delegate = ComboBoxDelegate(val_list, self.item_view)
            combo_delegate.set_model(self.src_model)
            self.item_view.setItemDelegateForColumn(col_idx, combo_delegate)

        for col_idx, val_list in self.src_model.get_spinbox_delegate_info().items():
            spin_delegate = SpinBoxDelegate(*val_list, self.item_view)
            spin_delegate.set_model(self.src_model)
            self.item_view.setItemDelegateForColumn(col_idx, spin_delegate)

    def get_selected_indexes(self):
        """
        Common
        :return:
        """
        # the indexes of proxy model
        selected_indexes = self.item_view.selectedIndexes()
        is_valid_indexes = []
        rows = []
        for idx in selected_indexes:
            is_valid_indexes.append(idx.isValid())
            rows.append(idx.row())

        if len(selected_indexes) > 0 and False not in is_valid_indexes:
            logger.debug(f"Indexes selected: {rows}")
            return selected_indexes
        else:
            logger.debug(f"Indexes not selected or invalid: {selected_indexes}")
            return None

    def change_rows(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'changed' in flag column and allowing the user
        to modify the item
        :param indexes:
        :return:
        """
        # only the first column indexes in the selected rows are
        # collected
        row_indexes = [self.prx_model.mapToSource(idx) for idx in indexes
                       if idx.column() == 0]
        logger.debug(f"rows{[idx.row() for idx in row_indexes]} being changed")
        for idx in row_indexes:
            self.src_model.set_chg_flag(idx)

    def delete_rows(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        """
        del_indexes = [self.prx_model.mapToSource(idx) for idx in indexes
                       if idx.column() == 0]
        logger.debug(f"rows{[idx.row() for idx in del_indexes]} being deleted")

        if len(del_indexes) > 0:
            self.src_model.set_del_flag(del_indexes)

    @Slot(object)
    def save_model_to_db(self, input_db_record: dict = None):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        try:
            if input_db_record is not None:
                self.src_model.append_new_row(**input_db_record)
            # if hasattr(self.parent.parent, "async_start"):
            #     self.parent.async_start(self.src_model.table_name)
                sig_txt = self.src_model.table_name + "_save"
                self.async_helper.async_start_signal.emit(sig_txt)
        except Exception as e:
            logger.debug('Failed saving sessions')
            logger.exception(e)
            QMessageBox.information(self.parent,
                                    "Failed saving sessions",
                                    str(e),
                                    QMessageBox.Close)

    def set_col_width(self, col_name: str, width: int):
        if isinstance(self.item_view, QTableView):
            self.item_view.setColumnWidth(self.src_model.get_col_number(col_name), width)
