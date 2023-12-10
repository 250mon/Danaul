import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from model.di_data_model import DataModel
from common.d_logger import Logs
from constants import EditLevel
from constants import RowFlags
from db.ds_lab import Lab


logger = Logs().get_logger("main")


class ModalityModel(DataModel):
    def __init__(self, modality_name: str):
        self.init_params()
        super().__init__(modality_name)

    def init_params(self):
        self.set_table_name('modalities')

        self.col_edit_lvl = {
            'category_name': EditLevel.AdminModifiable,
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

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        columns_for_delegate = ['category_name']
        delegate_info = [self.get_col_number(c) for c in columns_for_delegate]
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
            int_type_columns = ['category_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            else:
                return str(data_to_display)

        elif role == Qt.TextAlignmentRole:
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
        logger.debug("Making a new category row ... ")
        logger.debug(kwargs)

        try:
            name: str = kwargs.get('modality_name')
            price: str = kwargs.get('modality_price', 0)
            category_name = kwargs.get('category_name')
            category_id = Lab().get_id_from_data('active_categorys',
                                                 {'category_name': category_name},
                                                 'category_id')
            description = kwargs.get('description', "")

            new_model_df = pd.DataFrame([{
                'active': active,
                'modality_name': name,
                'modality_price': price,
                'category_id': category_id,
                'category_name': category_name,
                'description': description,
                'flag': RowFlags.NewRow
            }])
            return new_model_df

        except Exception as e:
            logger.debug("New modality info is improper!")
            logger.debug(e)
