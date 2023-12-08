from typing import List
from PySide6.QtWidgets import QMainWindow, QWidget, QMessageBox, QAbstractItemView
from PySide6.QtCore import QSortFilterProxyModel, QModelIndex
from model.di_data_model import DataModel
from ui.default_delegate import DefaultDelegate
from ui.combobox_delegate import ComboBoxDelegate
from ui.spinbox_delegate import SpinBoxDelegate
from common.d_logger import Logs

logger = Logs().get_logger("main")


class ItemViewHelpers:
    def __init__(self,
                 src_model: DataModel,
                 proxy_model: QSortFilterProxyModel,
                 view: QAbstractItemView,
                 parent: QWidget = None):
        self.parent: QMainWindow = parent
        self.src_model = src_model
        self.prx_model = proxy_model
        self.item_view = view
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
        to modify the treatments
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.src_model.is_flag_column(idx):
                src_idx = self.prx_model.mapToSource(idx)
                self.src_model.set_chg_flag(src_idx)
                logger.debug(f"rows {src_idx.row()} being changed")

    def delete_rows(self, indexes: List[QModelIndex]):
        """
        Common
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        """
        del_indexes = []
        for idx in indexes:
            # do it only once for multiple indexes belonging to the same row
            if self.src_model.is_flag_column(idx):
                src_idx = self.prx_model.mapToSource(idx)
                del_indexes.append(src_idx)

        if len(del_indexes) > 0:
            self.src_model.set_del_flag(del_indexes)
            rows = [idx.row() for idx in del_indexes]
            logger.debug(f"rows {rows} deleted")

    def filter_for_selected_id(self, id: int):
        """
        A double click event that triggers the upper level widget's
        row_selected method eventually calls this method
        :param treatment_id:
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        self.src_model.del_new_rows()
        # let the model learn the upper model index for a new row creation
        self.src_model.set_upper_model_id(id)

        # filtering in the sku view
        self.prx_model.setFilterRegularExpression(
            f"^{self.src_model.selected_patient_id}$")

    def filter_for_search_all(self):

        """
        Connected to search all button
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        self.src_model.del_new_rows()
        self.src_model.set_upper_model_id(None)
        self.prx_model.setFilterRegularExpression("^\\d*$")

    def set_col_width(self, col_name:str, width: int):
        self.item_view.setColumnWidth(self.src_model.get_col_number(col_name), width)

    def set_col_hidden(self, left_most_hidden: str):
        left_most_col_num = self.src_model.get_col_number(left_most_hidden)
        last_col_num = len(self.src_model.column_names)
        for c in range(left_most_col_num, last_col_num):
            self.item_view.setColumnWidth(c, 1)
            # The following methods don't allow the hidden col
            # to be accessible
            # self.table_view.horizontalHeader().hideSection(c)
            # self.table_view.setColumnHidden(c, True)
            # filterAcceptsColumn..
