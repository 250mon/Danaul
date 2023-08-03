import os
import pandas as pd
from typing import Tuple, List
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

        column_names = ['item_id', 'item_valid', 'item_name', 'category_name',
                        'description', 'category_id', 'flag']
        self.set_column_names(column_names)

        col_edit_lvl = {
            'item_id': EditLevel.NotEditable,
            'item_valid': EditLevel.Modifiable,
            'item_name': EditLevel.Creatable,
            'category_name': EditLevel.Modifiable,
            'description': EditLevel.Modifiable,
            'category_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }
        self.set_column_edit_level(col_edit_lvl)

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['category_name'] = self.model_df['category_id'].map(Lab().category_name_s)
        self.model_df['flag'] = ''

    def editable_columns(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that are editable by user
        :return:
        """
        editable_cols = ['category_name', 'description']
        if self.user_name in ADMIN_GROUP:
            editable_cols += ['item_valid']
        return editable_cols
    
    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Returns values list and column index for creating combobox
        :return:
        """
        col_index = self.get_col_number(col_name)
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
        def is_deleted_row(index: QModelIndex) -> bool:
            return 'deleted' in self.model_df.iloc[index.row(), self.get_col_number('flag')]

        def is_valid_row(index: QModelIndex) -> bool:
            return self.model_df.iloc[index.row(), self.get_col_number('item_valid')]

        if not index.isValid():
            return None

        data_to_display = self.model_df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            int_type_columns = [self.get_col_number(c) for c in
                                ['item_id', 'category_id']]
            if index.column() in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            else:
                # otherwise, string type
                return str(data_to_display)

        elif role == Qt.BackgroundRole and is_deleted_row(index):
            return QBrush(Qt.darkGray)

        elif role == Qt.BackgroundRole and not is_valid_row(index):
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

        ret_value: object = value

        if index.column() == self.get_col_number('item_valid'):
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

        # Tell the pandas model whether the data is editable or not
        if self.model_df.iloc[index.row(), self.get_col_number('flag')] == 'new':
            # editing a newly created row
            self.set_edit_level(EditLevel.Creatable)
        else:
            # changing a row
            self.set_edit_level(EditLevel.Modifiable)
            self.set_chg_flag(index)

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
            'item_valid': True,
            'item_name': "",
            'category_name': cat_name,
            'description': "",
            'category_id': default_cat_id,
            'flag': 'new'
        }])
        return new_model_df

    def validate_new_row(self, index: QModelIndex) -> bool:
        """
        Needs to be implemented in subclasses
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