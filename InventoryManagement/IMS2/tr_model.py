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
        self.update_items_params()
        # setting a model is carried out in the DataModel
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('trs')

        column_names = ['tr_id', 'sku_id', 'tr_type', 'tr_qty', 'before_qty', 'after_qty'
                        'tr_timestamp', 'description', 'user_id', 'tr_type_id']
        self.set_column_names(column_names)

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
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_item_id(self, sku_id: int):
        self.selected_sku_id = sku_id

    async def update(self):
        await super().update()

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['tr_type'] = self.model_df['tr_type_id'].map(Lab().tr_type_name_s)
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
                value: str,
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

        obj_type_value: object = value

        if index.column() == self.get_col_number('active'):
            # taking care of converting str type input to bool type
            if value == 'True':
                obj_type_value = True
            else:
                obj_type_value: bool = False
        elif index.column() == self.get_col_number('sku_id'):
            if value in self.item_name_s.tolist():
                id_col = self.get_col_number('item_id')
                self.model_df.iloc[index.row(), id_col] = self.item_id_s.loc[value]
            else:
                logger.debug(f'setData: item_name({value}) is not valid')
                return False
        elif index.column() == self.get_col_number('item_size'):
            id_col = self.get_col_number('item_size_id')
            self.model_df.iloc[index.row(), id_col] = Lab().item_size_id_s.loc[value]
        elif index.column() == self.get_col_number('item_side'):
            id_col = self.get_col_number('item_side_id')
            self.model_df.iloc[index.row(), id_col] = Lab().item_side_id_s.loc[value]
        elif index.column() == self.get_col_number('expiration_date'):
            # data type is datetime.date
            if isinstance(value, QDate):
                obj_type_value = qdate_to_pydate(value)
        else:
            pass

        return super().setData(index, obj_type_value, role)

    def make_a_new_row_df(self, next_new_id) -> pd.DataFrame or None:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise None
        """
        if self.selected_sku_id is None:
            logger.error('make_a_new_row_df: item_id is empty')
            return None
        elif not self.active_s[self.selected_sku_id]:
            logger.error('make_a_new_row_df: item_id is not active')
            return None

        default_item_id = self.selected_sku_id
        item_name = self.item_name_s[default_item_id]
        logger.debug(f'make_a_new_row_df: {default_item_id} {item_name} being created')
        default_item_size_id = 1
        iz_name = Lab().item_size_name_s.loc[default_item_size_id]
        default_item_side_id = 1
        id_name = Lab().item_side_name_s.loc[default_item_side_id]

        new_model_df = pd.DataFrame([{
            'tr_id': next_new_id,
            'sku_id': self.selected_sku_id,
            'active': True,
            'tr_qty': 0,
            'min_qty': 2,
            'item_size': iz_name,
            'item_side': id_name,
            'expiration_date': 'DEFAULT',
            'description': "",
            'bit_code': 'A11',
            'item_id': default_item_id,
            'item_size_id': default_item_size_id,
            'item_side_id': default_item_side_id,
            'flag': 'new'
        }])
        return new_model_df
