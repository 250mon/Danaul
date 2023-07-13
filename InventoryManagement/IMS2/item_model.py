import os
import pandas as pd
from typing import List, Dict
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QBrush, QFont
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class ItemModel(PandasModel):
    def __init__(self, template_flag=False):
        super().__init__()
        # getting item data from db
        self.lab = Lab(InventoryDb('db_settings'))

        # need category_id to category_name mapping table
        self.category_df: pd.DataFrame = self.lab.categories_df

        # set data to model
        # mapping-table indicating where the actual column is located in the table
        self.column_names = ['item_id', 'item_valid', 'item_name',
                             'category_name', 'description', 'category_id',
                             'flag']

        if not template_flag:
            self.set_model_df()
        else:
            self.set_template_model_df()

        self.editable_col_idx = {col_name: self.model_df.columns.get_loc(col_name)
                                 for col_name in ['item_valid', 'category_name', 'description']}

    def set_model_df(self):
        # for category name mapping
        cat_df = self.category_df.set_index('category_id')
        cat_s: pd.Series = cat_df['category_name']

        self.model_df = self.lab.items_df
        self.model_df['category_name'] = self.model_df['category_id'].map(cat_s)
        self.model_df['flag'] = ''

        # reindexing in the order of table view
        self.model_df = self.model_df.reindex(self.column_names, axis=1)

    def set_template_model_df(self):
        self.model_df = pd.DataFrame([(-1, True, "", 1, "", self.category_df.iat[0, 1], 'new')],
                              columns=self.column_names)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """Override method from QAbstractTableModel

        QTableView accepts only QString as input for display

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        data_to_display = self.model_df.iloc[index.row(), index.column()]
        if data_to_display is None:
            return None

        flag_col_index = self.model_df.columns.get_loc('flag')
        is_deleted = 'deleted' in self.model_df.iloc[index.row(), flag_col_index]
        valid_col_index = self.model_df.columns.get_loc('item_valid')
        is_valid = self.model_df.iloc[index.row(), valid_col_index]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(data_to_display)

        # for sorting, use Qt.UserRole
        elif role == Qt.UserRole:
            int_type_columns = [self.model_df.columns.get_loc(c) for c in
                                ['item_id', 'item_valid', 'category_id']]
            # if column data is int, return int type
            if index.column() in int_type_columns:
                return int(data_to_display)
            # otherwise, string type
            else:
                return data_to_display

        elif role == Qt.BackgroundRole and is_deleted:
            return QBrush(Qt.darkGray)

        elif role == Qt.BackgroundRole and not is_valid:
            return QBrush(Qt.lightGray)

        else:
            return None

    def setData(self,
                index: QModelIndex,
                value: str,
                role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f'setData({index}, {value})')
        # taking care of converting str type input to bool type
        if index.column() == self.model_df.columns.get_loc('item_valid'):
            val: bool = False
            if value == 'True':
                val = True
        elif index.column() == self.model_df.columns.get_loc('category_name'):
            # for category name mapping
            cat_df = self.category_df.set_index('category_name')
            cat_s: pd.Series = cat_df['category_id']
            self.model_df.iloc[index.row(),
                    self.model_df.columns.get_loc('category_id')] = cat_s.loc[value]
            val: object = value
        else:
            val: object = value

        # setting new data is followed by setting change flag
        self.set_chg_flag(index)

        return super().setData(index, val, role)

    def set_chg_flag(self, index: QModelIndex):
        '''
        set the flag of the row to which the index belongs
        :param index:
        :return:
        '''
        flag_col_index = index.siblingAtColumn(self.model_df.columns.get_loc('flag'))
        current_msg = self.data(flag_col_index)
        if 'changed' not in current_msg:
            new_msg = current_msg + ' changed'
            super().setData(flag_col_index, new_msg)

    def set_del_flag(self, index: QModelIndex):
        '''

        :param index:
        :return:
        '''
        current_msg: str = self.data(index)
        if 'deleted' in current_msg:
            new_msg = current_msg.replace(' deleted', '')
            self.setData(index, new_msg)
            return False
        else:
            new_msg = current_msg + ' deleted'
            self.setData(index, new_msg)
            return True

    def add_new_row(self, new_df: pd.DataFrame) -> str:
        new_item_name = new_df.at[0, 'item_name']
        if self.model_df[self.model_df.item_name == new_item_name].empty:
            new_df['item_id'] = self.model_df['item_id'].max() + 1
            self.model_df = pd.concat([self.model_df, new_df])
            result_msg = f'Successfully add Item [{new_item_name}]'
            logger.debug(result_msg)
            return result_msg
        else:
            result_msg = f'Failed to add Item [{new_item_name}]: Duplicate item name'
            logger.warning(result_msg)
            return result_msg

    async def update_db(self):
        pass