import os
import pandas as pd
import asyncpg.exceptions
from typing import Dict, Tuple, List
from abc import abstractmethod
from PySide6.QtCore import Qt, QModelIndex
from pandas_model import PandasModel
from di_lab import Lab
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class DataModel(PandasModel):
    def __init__(self, user_name):
        super().__init__()
        # for access control
        self.user_name = user_name
        # for data name
        self.table_name = self.set_table_name()
        # columns to show in the table view
        self.column_names = self.set_column_names()
        # set editable columns
        self.editable_cols = self.set_editable_columns()
        # a list of columns which are used to make a df updating db
        self.db_column_names = None

        # set model df
        self.set_model_df()


    @abstractmethod
    def set_table_name(self):
        """
        Needs to be implemented in the subclasses
        Returns a talbe name specified in the DB
        :return:
        """

    @abstractmethod
    def set_column_names(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that show in the table view
        :return:
        """

    @abstractmethod
    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of auxiliary data
        :return:
        """

    @abstractmethod
    def set_editable_columns(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that are editable by user
        :return:
        """

    def set_editable_cols_to_model(self):
        """
        Sets up editable columns in the pandas model
        :return:
        """
        # set editable columns
        self.editable_col_iloc: Dict[str, int] = {
            col_name: self.model_df.columns.get_loc(col_name)
            for col_name in self.editable_cols
        }
        super().set_editable_columns(list(self.editable_col_iloc.values()))

    def set_model_df(self):
        """
        Makes DataFrame out of data received from DB
        :return:
        """
        logger.debug(f'set_model_df: setting {self.table_name}_model_f to the df of Lab')
        self.model_df = Lab().table_df[self.table_name]

        # we store the columns list here for later use of db update
        self.db_column_names = self.model_df.columns.tolist()

        # reindexing in the order of table view
        self.model_df = self.model_df.reindex(self.column_names, axis=1)

        # add name columns for ids of each auxiliary data
        self.set_add_on_cols()

        # set editable columns
        self.set_editable_cols_to_model()

    def set_filtered_model_df(self, query_str: str = ""):
        """
        Apply filter to model_df
        :param query_str:
        :return:
        """
        if False: #query_str != "":
            logger.debug(f'set_filtered_model_df: {query_str}')
            print(Lab().table_df['skus'])
            self.model_df = Lab().table_df['skus'].query(query_str)
            print('after')
            print(self.model_df['item_id'])

    @abstractmethod
    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Needs to be implemented in the subclasses
        Returns values list and column index for creating combobox
        :return:
        """
        # col_index = self.model_df.columns.get_loc(col_name)
        # if col_name == 'item_valid':
        #     val_list = ['True', 'False']
        # elif col_name == 'category_name':
        #     val_list = Lab().category_name_s.to_list()
        # else:
        #     val_list = None
        # return col_index, val_list

    async def update_model_df_from_db(self):
        """
        Receives data from DB and converts it to DF
        :return:
        """
        logger.debug(f'update_model_df_from_db: downloading data from DB')
        await Lab().update_lab_df_from_db(self.table_name)
        self.set_model_df()

    def add_new_row_by_delegate(self):
        """
        Adds a new row to the end
        :return:
        """
        print(self.model_df)
        next_new_id = self.model_df.iloc[:, 0].max() + 1
        print(f'add_new_row_by_delegate: New row id is {next_new_id}')

        new_row_df = self.make_a_new_row_df(next_new_id)
        self.model_df = pd.concat([self.model_df, new_row_df])

    @abstractmethod
    def make_a_new_row_df(self, next_new_id):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """
        # default_cat_id = 1
        # cat_name = Lab().category_name_s.loc[default_cat_id]
        # new_model_df = pd.DataFrame([(next_new_id, True, "", cat_name, "", default_cat_id, 'new')],
        #                             columns=self.column_names)
        # return new_model_df

    def set_new_flag(self, index: QModelIndex):
        """
        Sets a 'new' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.model_df.columns.get_loc('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)
        self.set_all_editable_row(index.row())

        super().setData(index, 'new')

    def set_chg_flag(self, index: QModelIndex):
        """
        Sets a 'changed' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.model_df.columns.get_loc('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg = self.data(index)
        if 'changed' not in current_msg:
            flag = current_msg + ' changed'
            super().setData(index, flag)

    def set_del_flag(self, index: QModelIndex):
        """
        Sets a 'deleted' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.model_df.columns.get_loc('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg: str = self.data(index)
        if 'deleted' in current_msg:
            flag = current_msg.replace(' deleted', '')
        else:
            flag = current_msg + ' deleted'

        self.unset_uneditable_row(index.row())
        super().setData(index, flag)

    async def update_db(self):
        """
        Updates DB reflecting the changes made to model_df
        :return:
        """
        logger.debug('update_db: Saving to DB ...')
        return_msg = None

        del_df = self.model_df.loc[self.model_df.flag.str.contains('deleted'), :]
        if not del_df.empty:
            logger.debug(f'{del_df}')
            # if flag contains 'new', just drop it
            del_df.drop(del_df[del_df.flag.str.contains('new')].index)
            df_to_upload = del_df.loc[:, self.db_column_names]
            results = await Lab().delete_df(self.table_name, df_to_upload)
            logger.debug(f'update_db: results of deleting = {results}')
            msg_list = []
            for i, result in enumerate(results, start=1):
                if isinstance(result, asyncpg.exceptions.ForeignKeyViolationError):
                    msg_list.append(f'{i}: Item ID is in use, Cannot be deleted')
                else:
                    msg_list.append(f'{i}: {result}')
            return_msg = '\n'.join(msg_list)
            self.model_df.drop(del_df.index, inplace=True)

            # reset all_editable_row for new rows
            self.unset_uneditable_row(-1)

        new_df = self.model_df.loc[self.model_df.flag.str.contains('new'), :]
        if not new_df.empty:
            logger.debug(f'{new_df}')
            df_to_upload = new_df.loc[:, self.db_column_names]
            # set id default to let DB assign an id without collision
            df_to_upload.iloc[:, 0] = 'DEFAULT'
            results = await Lab().insert_df(self.table_name, df_to_upload)
            logger.debug(f'update_db: results of inserting new rows = {results}')

            # reset all_editable_row for new rows
            self.unset_all_editable_row(-1)

        chg_df = self.model_df.loc[self.model_df.flag.str.contains('changed'), :]
        if not chg_df.empty:
            logger.debug(f'{chg_df}')
            df_to_upload = chg_df.loc[:, self.db_column_names]
            results = await Lab().update_df(self.table_name, df_to_upload)
            logger.debug(f'update_db: results of changing = {results}')

        return return_msg