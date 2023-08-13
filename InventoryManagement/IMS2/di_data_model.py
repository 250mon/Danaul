import os
import pandas as pd
import asyncpg.exceptions
from typing import Dict, List
from abc import abstractmethod
from PySide6.QtCore import QModelIndex, Qt
from pandas_model import PandasModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import EditLevel, RowFlags, ADMIN_GROUP


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
        if self.user_name in ADMIN_GROUP:
            self.usr_edit_lvl = EditLevel.AdminModifiable
        else:
            self.usr_edit_lvl = EditLevel.UserModifiable
        self.set_edit_level(self.usr_edit_lvl)
        # a list of columns which are used to make a df updating db
        self.db_column_names = None

        # set model df
        self._set_model_df()

        self.selected_upper_index = None
        self.selected_upper_id = None

    def set_table_name(self, table_name: str):
        self.table_name = table_name

    def set_column_names(self, column_names: List[str]):
        self.column_names = column_names

    def set_column_index_edit_level(self, col_edit_lvl: Dict[str, EditLevel]):
        """
        Converts column name to column index in the Dict
        And register it to the Pandas model
        :param col_edit_lvl:
        :return:
        """
        col_idx_edit_lvl = {}
        for col_name, lvl in col_edit_lvl.items():
            col_idx = self.column_names.index(col_name)
            col_idx_edit_lvl[col_idx] = lvl
        super().set_column_index_edit_level(col_idx_edit_lvl)

    def set_upper_model_index(self, index: QModelIndex or None):
        """
        Needs to be implemented if necessary
        upper model index is used for filtering
        :param index:
        :return:
        """
        pass

    def get_col_number(self, col_name: str) -> int:
        return self.model_df.columns.get_loc(col_name)

    def get_col_name(self, col_num: int) -> str:
        return self.model_df.columns[col_num]

    def is_flag_column(self, index: QModelIndex) -> bool:
        flag_col = self.get_col_number('flag')
        return index.column() == flag_col

    def get_flag(self, index: QModelIndex) -> int:
        """
        Returns the flag of the row where the index belongs to
        :param index:
        :return: flag
        """
        flag = self.model_df.iloc[index.row(), self.get_col_number('flag')]
        return flag

    def set_flag(self, index: QModelIndex, flag: int):
        """
        Set the flag to the row where the index belongs to
        :param index:
        :param flag:
        :return:
        """
        self.model_df.iloc[index.row(), self.get_col_number('flag')] = flag

    def is_active_row(self, index: QModelIndex) -> bool:
        return self.model_df.iloc[index.row(), self.get_col_number('active')]

    @abstractmethod
    def set_add_on_cols(self) -> None:
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of auxiliary data
        :return:
        """

    def _set_model_df(self):
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

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        return []

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        return {}

    def get_spinbox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the spinbox
        for spinbox delegate
        :return:
        """
        return {}

    async def update_model_df_from_db(self):
        """
        Receives data from DB and converts it to DF
        :return:
        """
        logger.debug(f'update_model_df_from_db: downloading data from DB')
        await Lab().update_lab_df_from_db(self.table_name)
        self._set_model_df()

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    async def update(self):
        """
        Update the model whenever relevant DB data changes
        Called by inventory_view
        If there needs any model specific update, it's implemented in
        the subclasses
        :return:
        """
        await self.update_model_df_from_db()

    def setData(self,
                index: QModelIndex,
                value: object,
                role=Qt.EditRole):

        if self.get_flag(index) == 'deleted':
            logger.debug(f'setData: Cannot change data in the deleted row')
            return

        return super().setData(index, value, role)

    def append_new_row(self, **kwargs) -> bool:
        """
        Appends a new row to the end of the model
        :return: True if succeeded or False
        """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())

        next_new_id = self.model_df.iloc[:, 0].max() + 1
        logger.debug(f'append_new_row: New model_df_row id is {next_new_id}')
        new_row_df = self.make_a_new_row_df(next_new_id, **kwargs)
        if new_row_df is None:
            return False
        self.model_df = pd.concat([self.model_df, new_row_df], ignore_index=True)

        self.endInsertRows()

        # handles model flags
        self.set_editable_new_row(self.rowCount() - 1)
        return True

    @abstractmethod
    def make_a_new_row_df(self, next_new_id, **kwargs):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """

    def drop_rows(self, indexes: List[QModelIndex]):
        id_col = 0
        ids = []
        for idx in indexes:
            if idx.column() != id_col:
                id = int(idx.siblingAtColumn(id_col).data())
            else:
                id = int(idx.data())
            ids.append(id)

        if len(ids) > 0:
            self.model_df.drop(self.model_df[self.model_df.iloc[:, 0].isin(ids)].index, inplace=True)
            logger.debug(f'drop_rows: model_df dropped ids {ids}')

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def diff_row(self, index: QModelIndex) -> bool:
        """
        Compare the df against the original data which is stored
        in the Lab
        :param index:
        :return: True if any difference or False if same
        """
        original_row = Lab().table_df[self.table_name].iloc[[index.row()], :]
        current_row = self.model_df.loc[self.model_df.index[[index.row()]],
                                         original_row.columns]
        if original_row.compare(current_row).empty:
            return False
        else:
            return True

    def set_chg_flag(self, index: QModelIndex):
        """
        Sets a 'changed' flag in the flag column of the row of index
        :param index:
        :return:
        """
        curr_flag = self.get_flag(index)
        curr_flag |= RowFlags.ChangedRow
        if self.diff_row(index):
            self.set_flag(index, curr_flag)

    def set_del_flag(self, index: QModelIndex):
        """
        Sets a 'deleted' flag in the flag column of the row of index
        :param index:
        :return:
        """
        curr_flag = self.get_flag(index)
        # exclusive or op with deleted flag
        curr_flag ^= RowFlags.DeletedRow
        self.set_flag(index, curr_flag)

        if curr_flag & RowFlags.DeletedRow:
            self.set_uneditable_row(index.row())
        else:
            self.set_uneditable_row(index.row())

    def get_new_df(self) -> pd.DataFrame:
        return self.model_df.loc[self.model_df['flag'] & RowFlags.NewRow > 0, :]

    def get_deleted_df(self) -> pd.DataFrame:
        return self.model_df.loc[self.model_df['flag'] & RowFlags.DeletedRow > 0, :]

    def get_changed_df(self) -> pd.DataFrame:
        return self.model_df.loc[self.model_df['flag'] & RowFlags.ChangedRow > 0, :]

    async def save_to_db(self):
        """
        Updates DB reflecting the changes made to model_df
        :return:
        """
        def make_return_msg(total_results: Dict[str, str or None]):
            messages = {}
            # total_results are composed of 3 results: new, chg, del
            # Each result are composed of result from multiple queries
            for op_type, result in total_results.items():
                if result is None:
                    msg = '성공!!'
                elif isinstance(result, asyncpg.exceptions.ForeignKeyViolationError):
                    msg = f'항목이 현재 사용 중이므로 삭제할 수 없습니다.'
                elif isinstance(result, asyncpg.exceptions.UniqueViolationError):
                    msg = f'중복 데이터가 존재합니다. 항목 새로 만들기가 실패하였습니다.'
                else:
                    msg = str(result)

                messages[op_type] = msg

            return_msg = '<RESULTS>'
            for op_type, msg in messages.items():
                return_msg += ('\n' + op_type + ': ' + msg)
            return return_msg

        logger.debug('update_db: Saving to DB ...')

        total_results = {}

        del_df = self.get_deleted_df()
        logger.debug(f'update_db: del_df: \n{del_df}')
        if not del_df.empty:
            logger.debug(f'{del_df}')
            # if flag contains 'new', just drop it
            del_df.drop(del_df[del_df.flag & RowFlags.NewRow > 0].index)
            df_to_upload = del_df.loc[:, self.db_column_names]
            results_del = await Lab().delete_df(self.table_name, df_to_upload)
            total_results['삭제'] = results_del
            logger.debug(f'update_db: result of deleting = {results_del}')
            self.model_df.drop(del_df.index, inplace=True)
            self.clear_uneditable_rows()

        new_df = self.get_new_df()
        logger.debug(f'update_db: new_df: \n{new_df}')
        if not new_df.empty:
            logger.debug(f'{new_df}')
            df_to_upload = new_df.loc[:, self.db_column_names]
            # set id default to let DB assign an id without collision
            df_to_upload.iloc[:, 0] = 'DEFAULT'
            results_new = await Lab().insert_df(self.table_name, df_to_upload)
            total_results['추가'] = results_new
            self.clear_editable_new_rows()
            logger.debug(f'update_db: result of inserting new rows = {results_new}')

        chg_df = self.get_changed_df()
        logger.debug(f'update_db: chg_df: \n{chg_df}')
        if not chg_df.empty:
            logger.debug(f'{chg_df}')
            df_to_upload = chg_df.loc[:, self.db_column_names]
            results_chg = await Lab().update_df(self.table_name, df_to_upload)
            total_results['수정'] = results_chg
            self.clear_editable_rows()
            logger.debug(f'update_db: result of changing = {results_chg}')

        return_msg = make_return_msg(total_results)
        return return_msg

    def is_model_editing(self) -> bool:
        """
        Returns if any rows has flag column set
        :return:
        """
        return not self.model_df.loc[
            self.model_df['flag'] != RowFlags.OriginalRow,
            'flag'].empty
