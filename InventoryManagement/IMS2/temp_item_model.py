import os
import pandas as pd
import asyncpg.exceptions
from typing import Dict, Tuple, List
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QBrush, QFont
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import ADMIN_GROUP


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class TempItemModel(DataModel):
    def __init__(self, user_name, template_flag=False):
        super().__init__(user_name)

        if template_flag:
            self.model_df = self.make_a_new_row_df(-1)

    def set_table_name(self):
        """
        Needs to be implemented in the subclasses
        Returns a talbe name specified in the DB
        :return:
        """
        return 'items'

    def set_column_names(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that show in the table view
        :return:
        """
        column_names = ['item_id', 'item_valid', 'item_name', 'category_name',
                        'description', 'category_id', 'flag']
        return column_names

    def set_editable_columns(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that are editable by user
        :return:
        """
        editable_cols = ['category_name', 'description']
        if self.user_name in ADMIN_GROUP:
            editable_cols += ['item_valid']
        return editable_cols

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['category_name'] = self.model_df['category_id'].map(Lab().category_name_s)
        self.model_df['flag'] = ''

    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Returns values list and column index for creating combobox
        :return:
        """
        col_index = self.model_df.columns.get_loc(col_name)
        if col_name == 'item_valid':
            val_list = ['True', 'False']
        elif col_name == 'category_name':
            val_list = Lab().category_name_s.to_list()
        else:
            val_list = None
        return col_index, val_list

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        data_to_display = self.model_df.iloc[index.row(), index.column()]
        if data_to_display is None:
            return None

        flag_col_iloc: int = self.model_df.columns.get_loc('flag')
        is_deleted = 'deleted' in self.model_df.iloc[index.row(), flag_col_iloc]
        valid_col_iloc: int = self.model_df.columns.get_loc('item_valid')
        is_valid = self.model_df.iloc[index.row(), valid_col_iloc]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(data_to_display)

        # for sorting, use SortRole
        elif role == self.SortRole:
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
        # taking care of converting str type input to bool type
        if index.column() == self.model_df.columns.get_loc('item_valid'):
            val: bool = False
            if value == 'True':
                val = True
        elif index.column() == self.model_df.columns.get_loc('category_name'):
            # if setting category_name, automatically setting category_id accordingly
            cat_id_col = self.model_df.columns.get_loc('category_id')
            self.model_df.iloc[index.row(), cat_id_col] = Lab().category_id_s[value]
            val: object = value
        elif index.column() == self.model_df.columns.get_loc('item_name'):
            # when a new row is added, item_name needs to be checked if any duplicate
            if not self.model_df[self.model_df.item_name == value].empty:
                logger.debug(f'setData: item name({value}) is already in use')
                return False
            else:
                val: str = value
        else:
            val: object = value

        # Unless it is a new item, setting data is followed by setting change flag
        flag_col_iloc: int = self.model_df.columns.get_loc('flag')
        if self.model_df.iloc[index.row(), flag_col_iloc] != 'new':
            self.set_chg_flag(index)

        return super().setData(index, val, role)

    def make_a_new_row_df(self, next_new_id):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """
        default_cat_id = 1
        cat_name = Lab().category_name_s.loc[default_cat_id]
        new_model_df = pd.DataFrame([(next_new_id, True, "", cat_name, "", default_cat_id, 'new')],
                                    columns=self.column_names)
        return new_model_df

    def add_new_row_by_widget(self, new_df: pd.DataFrame) -> str:
        """
        Appends a new row of data to the model_df
        :param new_df:
        :return:
        """
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