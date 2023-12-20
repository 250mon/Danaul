import pandas as pd
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
from constants import RowFlags


logger = Logs().get_logger("main")


class BodyPartModel(DataModel):
    def __init__(self, part_name: str):
        self.init_params()
        super().__init__(part_name)

    def init_params(self):
        self.set_table_name('body_parts')

        self.col_edit_lvl = {
            'part_name': EditLevel.AdminModifiable,
            'sub_parts': EditLevel.AdminModifiable,
            'part_id': EditLevel.NotEditable,
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
            int_type_columns = ['part_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            else:
                return str(data_to_display)

        elif role == Qt.TextAlignmentRole:
            left_aligned = ['sub_parts']
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

        return super().setData(index, value, role)

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        logger.debug("Making a new body_part row ... ")
        logger.debug(kwargs)

        try:
            name: str = kwargs.get('part_name')
            sub_parts = kwargs.get('sub_parts', "")

            new_model_df = pd.DataFrame([{
                'part_id': 0,  # any number is ok, getting replaced by DEFAULT
                'part_name': name,
                'sub_parts': sub_parts,
                'flag': RowFlags.NewRow
            }])
            return new_model_df

        except Exception as e:
            logger.debug("New body_part info is improper!")
            logger.debug(e)

    def is_part_name_duplicate(self, part_name: str) -> bool:
        if (self.model_df.empty or
                self.model_df.query(f"part_name == '{part_name}'").empty):
            return False
        else:
            return True
