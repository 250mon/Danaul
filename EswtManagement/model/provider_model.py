import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
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
            'provider_name': EditLevel.NotEditable,
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

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        col_name = self.get_col_name(index.column())
        data_to_display = self.model_df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            int_type_columns = ['provider_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            else:
                return str(data_to_display)

        elif role == Qt.TextAlignmentRole:
            left_aligned = ['description']
            if col_name in left_aligned:
                return Qt.AlignLeft
            else:
                return Qt.AlignCenter

        else:
            return super().data(index, role)

    def setData(self,
                index: QModelIndex,
                value: object,
                role=Qt.EditRole):
        # provider_model does not alter the data
        pass

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        # provider_model does not alter the data
        pass
