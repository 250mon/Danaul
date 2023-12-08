import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
from constants import RowFlags


logger = Logs().get_logger("main")


class UserModel(DataModel):
    def __init__(self, user_name: str):
        self.init_params()
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('users')

        self.col_edit_lvl = {
            'user_id': EditLevel.NotEditable,
            'active': EditLevel.AdminModifiable,
            # 'user_password': EditLevel.NotEditable,
            'user_realname': EditLevel.NotEditable,
            'user_job': EditLevel.NotEditable,
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

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        delegate_info = {
            self.get_col_number('active'): [True, False]
        }
        return delegate_info

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
            int_type_columns = ['user_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            elif col_name == 'active':
                if data_to_display:
                    return 'Y'
                else:
                    return 'N'
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
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f"index({index}), value({value})")

        col_name = self.get_col_name(index.column())
        if col_name == 'active':
            # taking care of converting str type input to bool type
            if value == 'Y':
                value = True
            else:
                value = False

        return super().setData(index, value, role)

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        emr_id: int = kwargs.get('user_emr_id')
        duplicate_emr_id = self.model_df.query(f"user_emr_id == {emr_id}")
        if not duplicate_emr_id.empty():
            error = f"user_emr_id({emr_id}) is duplicate"
            raise DuplicateUserEmrId(error)

        try:
            name: str = kwargs.get('user_name')
            gender: str = kwargs.get('user_gender')

            new_model_df = pd.DataFrame([{
                'user_emr_id': emr_id,
                'user_name': name,
                'user_gender': gender,
                'flag': RowFlags.NewRow
            }])
            return new_model_df
        except Exception as e:
            logger.debug("New user info is improper!")
            logger.debug(e)
