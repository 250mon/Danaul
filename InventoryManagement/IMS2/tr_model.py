import os
import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QBrush, QFont
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import EditLevel
from datetime_utils import *

logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""


class TrModel(DataModel):
    def __init__(self, user_name: str):
        self.init_params()
        self.selected_sku_id = None
        self.update_skus_params()
        # setting a model is carried out in the DataModel
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('transactions')

        self.col_edit_lvl = {
            'tr_id': EditLevel.NotEditable,
            'sku_id': EditLevel.NotEditable,
            'tr_type': EditLevel.Creatable,
            'tr_qty': EditLevel.Creatable,
            'before_qty': EditLevel.NotEditable,
            'after_qty': EditLevel.NotEditable,
            'tr_timestamp': EditLevel.Creatable,
            'description': EditLevel.UserModifiable,
            'user_name': EditLevel.Creatable,
            'tr_type_id': EditLevel.NotEditable,
            'user_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_sku_id(self, sku_id: int):
        self.selected_sku_id = sku_id

    def update_skus_params(self):
        skus_df = Lab().table_df['skus'].loc[:, ['sku_id', 'active', 'bit_code', 'sku_qty']]
        skus_df_id_indexed = skus_df.set_index('sku_id')
        self.sku_active_s: pd.Series = skus_df_id_indexed.iloc[:, 0]
        self.sku_bitcode_s: pd.Series = skus_df_id_indexed.iloc[:, 1]
        self.sku_qty_s: pd.Series = skus_df_id_indexed.iloc[:, 2]

    async def update(self):
        await super().update()

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['tr_type'] = self.model_df['tr_type_id'].map(Lab().tr_type_s)
        self.model_df['user_name'] = self.model_df['user_id'].map(Lab().user_name_s)
        self.model_df['flag'] = ''

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in ['description']]
        return default_info_list

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        col_name = self.get_col_name(index.column())
        data_to_display = self.model_df.iloc[index.row(), index.column()]
        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            int_type_columns = ['tr_id', 'user_id', 'sku_id', 'tr_type_id',
                                'tr_qty', 'before_qty', 'after_qty']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            elif col_name == 'tr_timestamp':
                # data type is datetime.date
                return pydt_to_qdt(data_to_display)
            else:
                # otherwise, string type
                return str(data_to_display)

        else:
            return None

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

        logger.debug(f'setData({index}, {value})')

        if index.column() == self.get_col_number('tr_timestamp'):
            # data type is datetime.date
            if isinstance(value, QDateTime):
                value = qdt_to_pydt(value)

        return super().setData(index, value, role)

    def make_a_new_row_df(self, next_new_id, **kwargs) -> pd.DataFrame or None:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise None
        """
        if self.selected_sku_id is None:
            logger.error('make_a_new_row_df: sku_id is empty')
            return None
        elif not self.sku_active_s[self.selected_sku_id]:
            logger.error('make_a_new_row_df: sku_id is not active')
            return None

        current_qty = self.sku_qty_s[self.selected_sku_id]
        tr_type = kwargs['tr_type']
        tr_type_id = Lab().tr_type_id_s.loc[tr_type]
        user_id = Lab().user_id_s[self.user_name]

        new_model_df = pd.DataFrame([{
            'tr_id': next_new_id,
            'sku_id': self.selected_sku_id,
            'tr_type': tr_type,
            'tr_qty': 0,
            'before_qty': current_qty,
            'after_qty': current_qty,
            'tr_timestamp': 'DEFAULT',
            'description': "",
            'user_name': self.user_name,
            'user_id': user_id,
            'tr_type_id': tr_type_id,
            'flag': 'new'
        }])
        return new_model_df