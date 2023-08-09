import os
import pandas as pd
from typing import Dict, List, Tuple
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QBrush, QFont
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import ADMIN_GROUP, EditLevel


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class ItemModel(DataModel):
    def __init__(self, user_name):
        self.init_params()
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('items')

        column_names = ['item_id', 'active', 'item_name', 'category_name',
                        'description', 'category_id', 'flag']
        self.set_column_names(column_names)

        self.column_edit_level = {
            'item_id': EditLevel.NotEditable,
            'active': EditLevel.AdminModifiable,
            'item_name': EditLevel.Creatable,
            'category_name': EditLevel.UserModifiable,
            'description': EditLevel.UserModifiable,
            'category_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }
        self.set_column_index_edit_level(self.column_edit_level)

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['category_name'] = self.model_df['category_id'].map(Lab().category_name_s)
        self.model_df['flag'] = ''

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in ['item_name', 'description']]
        return default_info_list

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        combo_info_dict = {
            self.get_col_number('active'): ['True', 'False'],
            self.get_col_number('category_name'): Lab().category_name_s.to_list()
        }
        return combo_info_dict

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        col_name = self.get_col_name(index.column())
        data_to_display = self.model_df.iloc[index.row(), index.column()]
        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            int_type_columns = ['item_id', 'category_id']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            else:
                # otherwise, string type
                return str(data_to_display)

        # elif role == Qt.BackgroundRole:
        #     if self.is_row_type(index, 'deleted'):
        #         return QBrush(Qt.darkGray)
        #     elif not self.is_active_row(index):
        #         return QBrush(Qt.lightGray)
        #     elif self.is_row_type(index, 'new'):
        #         if self.column_edit_level[col_name] <= EditLevel.Creatable:
        #             return QBrush(Qt.yellow)
        #         else:
        #             return QBrush(Qt.darkYellow)
        #     elif self.is_row_type(index, 'changed'):
        #         if self.column_edit_level[col_name] <= self.edit_level:
        #             return QBrush(Qt.green)
        #         else:
        #             return QBrush(Qt.darkGreen)

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

        ret_value: object = value

        if index.column() == self.get_col_number('active'):
            # taking care of converting str type input to bool type
            ret_value: bool = False
            if value == 'True':
                ret_value = True
        elif index.column() == self.get_col_number('category_name'):
            # if setting category_name, automatically setting category_id accordingly
            cat_id_col = self.get_col_number('category_id')
            self.model_df.iloc[index.row(), cat_id_col] = Lab().category_id_s[value]
        elif index.column() == self.get_col_number('item_name'):
            # when a new row is added, item_name needs to be checked if any duplicate
            if not self.model_df[self.model_df.item_name == value].empty:
                logger.debug(f'setData: item name({value}) is already in use')
                return False
        else:
            pass

        return super().setData(index, ret_value, role)

    def make_a_new_row_df(self, next_new_id):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """
        default_cat_id = 1
        cat_name = Lab().category_name_s.loc[default_cat_id]
        new_model_df = pd.DataFrame([{
            'item_id': next_new_id,
            'active': True,
            'item_name': "",
            'category_name': cat_name,
            'description': "",
            'category_id': default_cat_id,
            'flag': 'new'
        }])
        return new_model_df

    def validate_new_row(self, index: QModelIndex) -> bool:
        """
        This is used to validate a new row generated by SingleItemWindow
        when the window is done with creating a new row and emits add_item_signal
        :param index:
        :return:
        """
        item_name_col = self.get_col_number('item_name')
        new_item_name = index.siblingAtColumn(item_name_col).data()
        if (new_item_name is not None and
                new_item_name != "" and
                new_item_name not in self.model_df['item_name']):
            logger.debug(f"validate_new_item: item_name {new_item_name} is valid")
            return True
        else:
            logger.debug(f"validate_new_item: item_name {new_item_name} is not valid")
            return False