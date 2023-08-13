import os
import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from datetime_utils import *
from item_model import ItemModel
from constants import RowFlags, EditLevel

logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""


class SkuModel(DataModel):
    def __init__(self, user_name: str, item_model: ItemModel):
        self.item_model = item_model
        self.init_params()
        self.update_items_params()
        # setting a model is carried out in the DataModel
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('skus')

        self.col_edit_lvl = {
            'sku_id': EditLevel.NotEditable,
            'representative': EditLevel.UserModifiable,
            'item_name': EditLevel.NotEditable,
            'sub_name': EditLevel.UserModifiable,
            'active': EditLevel.AdminModifiable,
            'sku_qty': EditLevel.Creatable,
            'min_qty': EditLevel.UserModifiable,
            'expiration_date': EditLevel.Creatable,
            'description': EditLevel.UserModifiable,
            'bit_code': EditLevel.AdminModifiable,
            'sku_name': EditLevel.NotEditable,
            'item_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }
        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_upper_model_index(self, item_model_index: QModelIndex or None):
        self.selected_upper_index = item_model_index

        if item_model_index is not None:
            self.selected_upper_id = item_model_index.siblingAtColumn(
                self.item_model.get_col_number('item_id')).data()
        else:
            self.selected_upper_id = None

    def update_items_params(self):
        items_df = Lab().table_df['items'].loc[:, ['item_id', 'item_name', 'active']]
        self.item_name_s: pd.Series = items_df.set_index('item_id').iloc[:, 0]
        self.item_id_s: pd.Series = items_df.set_index('item_name').iloc[:, 0]
        self.item_active_s: pd.Series = items_df.set_index('item_id').iloc[:, 1]

    async def update(self):
        await super().update()
        self.update_items_params()

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['item_name'] = self.model_df['item_id'].map(self.item_name_s)
        self.model_df['sku_name'] = self.model_df['item_name'].str.cat(
            self.model_df.loc[:, 'sub_name'], na_rep="-", sep=" ").str.replace("None", "")
        self.model_df['flag'] = RowFlags.OriginalRow

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in
                             ['representative', 'sub_name', 'description', 'bit_code']]
        return default_info_list

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        combo_info_dict = {
            self.get_col_number('active'): ['Y', 'N'],
        }
        return combo_info_dict

    def get_spinbox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the spinbox
        for spinbox delegate
        :return:
        """
        spin_info_dict = {
            self.get_col_number('min_qty'): [0, 1000],
        }
        return spin_info_dict

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
            int_type_columns = ['sku_id', 'item_id', 'sku_qty', 'min_qty']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)

            elif col_name == 'expiration_date':
                # data type is datetime.date
                return pydate_to_qdate(data_to_display)

            elif col_name == 'active' or col_name == 'representative':
                if data_to_display:
                    return 'Y'
                else:
                    return 'N'

            else:
                # otherwise, string type
                return str(data_to_display)

        elif role == Qt.TextAlignmentRole:
            left_aligned = ['description']
            if col_name in left_aligned:
                return Qt.AlignLeft
            else:
                return Qt.AlignCenter

        # elif role == Qt.BackgroundRole:
        #     if self.is_row_type(index, 'deleted'):
        #         return QBrush(Qt.darkGray)
        #     elif not self.is_active_row(index):
        #         return QBrush(Qt.lightGray)
        #     elif self.is_row_type(index, 'new'):
        #         if self.col_edit_lvl[col_name] <= EditLevel.Creatable:
        #             return QBrush(Qt.yellow)
        #         else:
        #             return QBrush(Qt.darkYellow)
        #     elif self.is_row_type(index, 'changed'):
        #         if self.col_edit_lvl[col_name] <= self.edit_level:
        #             return QBrush(Qt.green)
        #         else:
        #             return QBrush(Qt.darkGreen)

        else:
            return None

    def setData(self,
                index: QModelIndex,
                value: object,
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

        col_name = self.get_col_name(index.column())
        if col_name == 'active' or col_name == 'representative':
            # taking care of converting str type input to bool type
            if value == 'Y':
                value = True
            else:
                value = False

        elif col_name == 'item_name':
            if value in self.item_name_s.tolist():
                id_col = self.get_col_number('item_id')
                self.model_df.iloc[index.row(), id_col] = self.item_id_s.loc[value]
            else:
                logger.debug(f'setData: item_name({value}) is not valid')
                return False

        elif col_name == 'sub_name':
            item_name_col = self.get_col_number('item_name')
            sku_name_col = self.get_col_number('sku_name')
            self.model_df.iloc[index.row(), sku_name_col] = ' '.join(
                [self.model_df.iloc[index.row(), item_name_col], value])

        elif col_name == 'expiration_date':
            # data type is datetime.date
            if isinstance(value, QDate):
                value = qdate_to_pydate(value)

        return super().setData(index, value, role)

    def make_a_new_row_df(self, next_new_id, **kwargs) -> pd.DataFrame or None:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise None
        """
        if self.selected_upper_id is None:
            logger.error('make_a_new_row_df: item_id is empty')
            return None
        elif not self.item_active_s[self.selected_upper_id]:
            logger.error('make_a_new_row_df: item_id is not active')
            return None

        default_item_id = self.selected_upper_id
        item_name = self.item_name_s[default_item_id]
        logger.debug(f'make_a_new_row_df: {default_item_id} {item_name} being created')
        exp_date = date(9999, 1, 1)

        new_model_df = pd.DataFrame([{
            'sku_id': next_new_id,
            'representative': True,
            'item_name': item_name,
            'sub_name': "",
            'active': True,
            'sku_qty': 0,
            'min_qty': 2,
            'expiration_date': exp_date,
            'description': "",
            'bit_code': "",
            'item_id': default_item_id,
            'flag': RowFlags.NewRow
        }])
        return new_model_df

    def update_sku_qty_after_transaction(self, index: QModelIndex, qty: int):
        logger.debug(f'update_sku_qty_after_transaction: {qty}')
        self.set_chg_flag(index)
        self.setData(index.siblingAtColumn(self.get_col_number('sku_qty')), qty)
        self.clear_editable_rows()
