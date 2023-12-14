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
            'modality_name': EditLevel.AdminModifiable,
            'active': EditLevel.AdminModifiable,
            'description': EditLevel.UserModifiable,
            'category_name': EditLevel.AdminModifiable,
            'modality_price': EditLevel.AdminModifiable,
            'modality_id': EditLevel.NotEditable,
            'category_id': EditLevel.NotEditable,
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
        category_df = Lab().table_df['category']
        self.category_info = category_df.loc[:, ['category_id', 'category_name']]
        self.model_df = self.model_df.merge(self.category_info,
                                            how='left',
                                            on='category_id')

        self.model_df['flag'] = RowFlags.OriginalRow

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        columns_for_delegate = ['modality_name', 'description']
        delegate_info = [self.get_col_number(c) for c in columns_for_delegate]
        return delegate_info

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        category_name_list = Lab().table_df['category']['category_name'].to_list()
        combo_info_dict = {
            self.get_col_number('category_name'): category_name_list,
        }
        return combo_info_dict

    def get_spinbox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the spinbox
        for spinbox delegate
        :return:
        """
        spin_info_dict = {
            self.get_col_number('modality_price'): [0, 500000],
        }
        return spin_info_dict

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
            int_type_columns = ['modality_id', 'category_id',
                                'modality_price']
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

        elif col_name == 'category_name':
            id_col_name = 'category_id'
            id_col = self.get_col_number(id_col_name)
            category_id = Lab().get_id_from_data('category',
                                                 {col_name: value},
                                                 id_col_name)
            self.model_df.iloc[index.row(), id_col] = category_id

        return super().setData(index, value, role)

    def make_a_new_row_df(self, **kwargs) -> pd.DataFrame:
        logger.debug("Making a new modality row ... ")
        logger.debug(kwargs)

        try:
            active: bool = kwargs.get('active', True)
            name: str = kwargs.get('modality_name')
            price: str = kwargs.get('modality_price', 0)
            category_name = kwargs.get('category_name')
            category_id = Lab().get_id_from_data('category',
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

    def is_modality_name_duplicate(self, modality_name: str) -> bool:
        if (self.model_df.empty or
                self.model_df.query(f"modality_name == '{modality_name}'").empty):
            return False
        else:
            return True
