import os
import pandas as pd
import asyncpg.exceptions
from typing import Dict, Tuple, List
from abc import abstractmethod
from PySide6.QtCore import QModelIndex
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


    def get_col_number(self, col_name):
        return self.model_df.columns.get_loc(col_name)

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
            col_name: self.get_col_number(col_name)
            for col_name in self.editable_cols
        }
        super().set_editable_columns(list(self.editable_col_iloc.values()))

    def set_model_df(self):
        """
        Makes DataFrame out of data received from DB
        :return:
        """
        logger.debug(f'set_model_df: setting the df of Lab to {self.table_name}_model_f')
        self.model_df = Lab().table_df[self.table_name]

        # we store the columns list here for later use of db update
        self.db_column_names = self.model_df.columns.tolist()

        # reindexing in the order of table view
        self.model_df = self.model_df.reindex(self.column_names, axis=1)

        # fill name columns against ids of each auxiliary data
        self.set_add_on_cols()

        # set editable columns
        self.set_editable_cols_to_model()

    @abstractmethod
    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Needs to be implemented in the subclasses
        Returns values list and column index for creating combobox
        :return:
        """

    async def update_model_df_from_db(self):
        """
        Receives data from DB and converts it to DF
        :return:
        """
        logger.debug(f'update_model_df_from_db: downloading data from DB')
        await Lab().update_lab_df_from_db(self.table_name)
        self.set_model_df()

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def add_new_row(self) -> QModelIndex:
        """
        Adds a new row to the end
        :return:
        """
        next_new_id = self.model_df.iloc[:, 0].max() + 1
        logger.debug(f'add_new_row: New model_df_row id is {next_new_id}')

        new_row_df = self.make_a_new_row_df(next_new_id)
        self.model_df = pd.concat([self.model_df, new_row_df], ignore_index=True)

        # TODO: needs to update how to get new_item_index
        row_count = self.rowCount()
        new_item_index = self.index(row_count - 1, 0)
        self.set_new_flag(new_item_index)

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

        return new_item_index

    @abstractmethod
    def make_a_new_row_df(self, next_new_id):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """

    @abstractmethod
    def validate_new_row(self, index: QModelIndex):
        """
        Needs to be implemented in subclasses
        :param index:
        :return:
        """

    def drop_rows(self, indexes: List[QModelIndex]):
        id_col = self.get_col_number('item_id')
        ids = []
        for idx in indexes:
            print(f'idx {idx}')
            if idx.column() != id_col:
                id = int(idx.siblingAtColumn(id_col).data())
                print(f'id {id}')
            else:
                id = int(idx.data())
                print(f'id {id}')
            ids.append(id)

        if len(ids) > 0:
            print(ids)
            print(self.model_df.iloc[:, 0])
            print(self.model_df.iloc[:, 0].isin(ids))
            self.model_df.drop(self.model_df[self.model_df.iloc[:, 0].isin(ids)].index, inplace=True)
            print(self.model_df)
            logger.debug(f'drop_items: model_df dropped item_id {ids}')

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def set_new_flag(self, index: QModelIndex):
        """
        Sets a 'new' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.get_col_number('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        super().setData(index, 'new')

        self.set_all_editable_row(index.row())

    def set_chg_flag(self, index: QModelIndex):
        """
        Sets a 'changed' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.get_col_number('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg = self.data(index)
        if 'changed' not in current_msg:
            flag = current_msg + ' changed'
            super().setData(index, flag)

        self.set_editable_row(index.row())

    def set_del_flag(self, index: QModelIndex):
        """
        Sets a 'deleted' flag in the flag column of the row of index
        :param index:
        :return:
        """
        flag_col_iloc = self.get_col_number('flag')
        if index.column() != flag_col_iloc:
            index: QModelIndex = index.siblingAtColumn(flag_col_iloc)

        current_msg: str = self.data(index)
        if 'deleted' in current_msg:
            flag = current_msg.replace(' deleted', '')
            self.unset_uneditable_row(index.row())
        else:
            flag = current_msg + ' deleted'
            self.set_uneditable_row(index.row())

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
                    msg_list.append(f'{i}: ID is in use, Cannot be deleted')
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

