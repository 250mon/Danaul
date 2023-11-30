import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
from common.datetime_utils import *
from constants import RowFlags


logger = Logs().get_logger("main")


class ProviderModel(DataModel):
    def __init__(self, user_name: str):
        self.init_params()
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('providers')

        self.col_edit_lvl = {
            'provider_id': EditLevel.NotEditable,
            'provider_name': EditLevel.AdminModifiable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_add_on_cols(self) -> None:
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['flag'] = RowFlags.OriginalRow

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        columns_for_delegate = ['provider_name']
        delegate_info = [self.get_col_number(c) for c in columns_for_delegate]
        return delegate_info

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        return super().data(index, role)

    def setData(self,
                index: QModelIndex,
                value: object,
                role=Qt.EditRole):
        """
        Override method from QAbstractTableModel
        :param index:
        :param value:
        :param role:
        :return:
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f"index({index}), value({value})")
        return super().setData(index, value, role)

    def make_a_new_row_df(self, next_new_id, **kwargs) -> pd.DataFrame:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise raise an exception
        """
        new_model_df = pd.DataFrame([{
            'provider_id': next_new_id,
            'provider_name': '',
            'flag': RowFlags.NewRow
        }])
        return new_model_df


def validate_new_row(self, index: QModelIndex) -> bool:
    """
    This is used to validate a new row generated by SingleItemWindow
    when the window is done with creating a new row and emits add_item_signal
    :param index:
    :return:
    """
    return True