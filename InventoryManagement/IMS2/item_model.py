import os
import pandas as pd
import asyncpg.exceptions
from typing import Dict, Tuple, List
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QBrush, QFont
from pandas_model import PandasModel
from di_lab import Lab
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

ADMIN_GROUP = ['admin', 'jye']

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class ItemModel(PandasModel):
    def __init__(self, user_name, template_flag=False):
        super().__init__()
        # for access control
        self.user_name = user_name

        # need category_id to category_name mapping table
        self.category_df: pd.DataFrame = Lab().table_df['category']

        # set data to model
        # mapping-table indicating where the actual column is located in the table
        self.column_names = ['item_id', 'item_valid', 'item_name',
                             'category_name', 'description', 'category_id',
                             'flag']
        # a list of column names which is used for db update
        self.db_column_names = None

        if not template_flag:
            self.set_model_df()
        else:
            self.set_template_model_df()

        self.set_editable_cols()

    def set_editable_cols(self):
        """
        Sets up editable columns in the pandas model
        :return:
        """
        # set editable columns
        if self.user_name in ADMIN_GROUP:
            editable_cols = ['item_valid', 'category_name', 'description']
        else:
            editable_cols = ['category_name', 'description']

        self.editable_col_iloc: Dict[str, int] = {
            col_name: self.model_df.columns.get_loc(col_name)
            for col_name in editable_cols
        }
        super().set_editable_cols(list(self.editable_col_iloc.values()))

    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Returns values list and column index for creating combobox
        :return:
        """
        col_index = self.model_df.columns.get_loc(col_name)
        if col_name == 'item_valid':
            val_list = ['True', 'False']
        elif col_name == 'category_name':
            val_list = self.category_df['category_name'].values.tolist()
        else:
            val_list = None
        return col_index, val_list

    async def update_model_df_from_db(self):
        """
        Receives data from DB and converts it to DF
        :return:
        """
        logger.debug(f'update_model_df_from_db')
        await Lab().update_lab_df_from_db('items')
        self.set_model_df()

    def set_model_df(self):
        """
        Makes DataFrame out of data received from DB
        :return:
        """
        # for category name mapping
        cat_df = self.category_df.set_index('category_id')
        cat_s: pd.Series = cat_df['category_name']

        logger.debug('set_model_df: setting item_model from lab.items_df')
        self.model_df = Lab().table_df['items']

        # we store the columns list here for later use of db update
        self.db_column_names = self.model_df.columns.tolist()

        # set more columns for the view
        self.model_df['category_name'] = self.model_df['category_id'].map(cat_s)
        self.model_df['flag'] = ''

        # reindexing in the order of table view
        self.model_df = self.model_df.reindex(self.column_names, axis=1)

    def set_template_model_df(self):
        """
        Called when a new item needs to be created.
        A template model has one row of new item
        :return:
        """
        self.model_df = pd.DataFrame([(-1, True, "", 1, "", self.category_df.iat[0, 1], 'new')],
                              columns=self.column_names)

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
            # for category name mapping
            cat_df = self.category_df.set_index('category_name')
            cat_s: pd.Series = cat_df['category_id']
            self.model_df.iloc[index.row(),
                    self.model_df.columns.get_loc('category_id')] = cat_s.loc[value]
            val: object = value
        else:
            val: object = value

        # Unless it is a new item, setting data is followed by setting change flag

        flag_col_iloc: int = self.model_df.columns.get_loc('flag')
        if self.model_df.iloc[index.row(), flag_col_iloc] != 'new':
            self.set_chg_flag(index)

        return super().setData(index, val, role)

    def add_new_row(self, new_df: pd.DataFrame) -> str:
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

    def set_chg_flag(self, index: QModelIndex):
        """
        Sets a 'changed' flag for the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.model_df.columns.get_loc('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg = self.data(index)
        if 'changed' not in current_msg:
            new_msg = current_msg + ' changed'
            super().setData(index, new_msg)

    def set_del_flag(self, index: QModelIndex):
        """
        Sets a 'deleted' flag for the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.model_df.columns.get_loc('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg: str = self.data(index)
        if 'deleted' in current_msg:
            new_msg = current_msg.replace(' deleted', '')
            super().setData(index, new_msg)
            self.unset_uneditable_row(index.row())
        else:
            new_msg = current_msg + ' deleted'
            super().setData(index, new_msg)
            self.set_uneditable_row(index.row())

    async def update_db(self):
        """
        Updates DB reflecting the changes made to model_df
        :return:
        """
        logger.debug('update_db: Saving to DB ...')
        return_msg = {}

        del_df: pd.DataFrame = self.model_df[self.model_df.flag.str.contains('deleted')]
        if not del_df.empty:
            logger.debug(f'{del_df}')
            # if flag contains 'new', just drop it
            del_df.drop(del_df[del_df.flag.str.contains('new')].index)
            df_to_upload = del_df[self.db_column_names]
            result = await Lab().delete_items_df(df_to_upload)
            logger.debug(f'update_db: result = {result}')
            if asyncpg.exceptions.ForeignKeyViolationError in result:
                return_msg['delete'] = 'Item ID is in use, Cannot be deleted'

            self.model_df.drop(del_df.index, inplace=True)

        new_df: pd.DataFrame = self.model_df[self.model_df.flag.str.contains('new')]
        if not new_df.empty:
            logger.debug(f'{new_df}')
            df_to_upload = new_df[self.db_column_names]
            result = await Lab().insert_items_df(df_to_upload)
            logger.debug(f'update_db: result = {result}')
            self.model_df.drop(new_df.index, inplace=True)

        chg_df: pd.DataFrame = self.model_df[self.model_df.flag.str.contains('changed')]
        if not chg_df.empty:
            logger.debug(f'{chg_df}')
            df_to_upload = chg_df[self.db_column_names]
            result = await Lab().upsert_items_df(df_to_upload)
            logger.debug(f'update_db: result = {result}')

        return return_msg