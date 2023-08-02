import os
import pandas as pd
from datetime import datetime, date
from typing import Dict, Tuple, List
from PySide6.QtCore import Qt, QModelIndex, QDate, QDateTime
from PySide6.QtGui import QBrush, QFont
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import ADMIN_GROUP


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class SkuModel(DataModel):
    def __init__(self, user_name: str):
        self._find_item_names_from_ids()
        super().__init__(user_name)

    def _find_item_names_from_ids(self):
        item_name_df = Lab().table_df['items'].loc[:, ['item_id', 'item_name']]
        self.item_name_s = item_name_df.set_index('item_id').iloc[:, 0]

    def table_name(self):
        """
        Needs to be implemented in the subclasses
        Returns a talbe name specified in the DB
        :return:
        """
        return 'skus'

    def column_names(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that show in the table view
        :return:
        """
        column_names = ['sku_id', 'item_name', 'sku_valid', 'sku_qty', 'min_qty',
                        'item_size', 'item_side', 'expiration_date', 'description',
                        'item_id', 'item_size_id', 'item_side_id', 'bit_code', 'flag']
        return column_names

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['item_size'] = self.model_df['item_size_id'].map(Lab().item_size_name_s)
        self.model_df['item_side'] = self.model_df['item_side_id'].map(Lab().item_side_name_s)
        self.model_df['item_name'] = self.model_df['item_id'].map(self.item_name_s)
        self.model_df['flag'] = ''

    def editable_columns(self):
        """
        Needs to be implemented in the subclasses
        Returns column names that are editable by user
        :return:
        """
        editable_cols = ['min_qty', 'description']
        if self.user_name in ADMIN_GROUP:
            editable_cols += ['sku_valid', 'expiration_date']
        return editable_cols

    def get_editable_cols_combobox_info(self, col_name: str) -> Tuple[int, List]:
        """
        Returns values list and column index for creating combobox
        :return:
        """
        col_index = self.model_df.columns.get_loc(col_name)
        if col_name == 'sku_valid':
            val_list = ['True', 'False']
        else:
            val_list = None
        return col_index, val_list

    def pydate_to_qdate(self, pydate: date):
        qdate = QDate.fromString(str(pydate), "yyyy-MM-dd")
        return qdate

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """
        Override method from QAbstractTableModel
        QTableView accepts only QString as input for display
        Returns data cell from the pandas DataFrame
        """
        def is_deleted_row(index: QModelIndex) -> bool:
            flag_col_iloc: int = self.get_col_number('flag')
            return 'deleted' in self.model_df.iloc[index.row(), flag_col_iloc]

        def is_valid_row(index: QModelIndex) -> bool:
            valid_col_iloc: int = self.get_col_number('sku_valid')
            return self.model_df.iloc[index.row(), valid_col_iloc]

        if not index.isValid():
            return None

        data_to_display = self.model_df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole or role == self.SortRole:
            int_type_columns = [self.get_col_number(c) for c in
                                ['sku_id', 'item_id', 'item_size_id',
                                 'item_side_id', 'sku_qty', 'min_qty']]
            if index.column() in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            elif index.column() == self.get_col_number('expiration_date'):
                # data type is datetime.date
                return self.pydate_to_qdate(data_to_display)
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

        if index.column() == self.model_df.columns.get_loc('sku_valid'):
            # taking care of converting str type input to bool type
            ret_value: bool = False
            if value == 'True':
                ret_value = True
        elif index.column() == self.model_df.columns.get_loc('item_size'):
            id_col = self.model_df.columns.get_loc('item_size_id')
            self.model_df.iloc[index.row(), id_col] = Lab().item_size_id_s.loc[value]
        elif index.column() == self.model_df.columns.get_loc('item_side'):
            id_col = self.model_df.columns.get_loc('item_side_id')
            self.model_df.iloc[index.row(), id_col] = Lab().item_side_id_s.loc[value]
        else:
            pass

        # Unless it is a new sku, setting data is followed by setting change flag
        flag_col_iloc: int = self.model_df.columns.get_loc('flag')
        if self.model_df.iloc[index.row(), flag_col_iloc] != 'new':
            self.set_chg_flag(index)

        return super().setData(index, ret_value, role)

    def make_a_new_row_df(self, next_new_id):
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return:
        """
        default_item_size_id = 1
        default_item_side_id = 1
        default_item_id = 1
        iz_name = Lab().item_size_name_s.loc[default_item_size_id]
        id_name = Lab().item_side_name_s.loc[default_item_side_id]
        item_name = self.item_name_s.loc[default_item_id]

        new_model_df = pd.DataFrame([{'sku_id': next_new_id,
                                      'item_name': item_name,
                                      'sku_valid': True,
                                      'sku_qty': 0,
                                      'min_qty': 2,
                                      'item_size': iz_name,
                                      'item_side': id_name,
                                      'expiration_date': 'DEFAULT',
                                      'description': "",
                                      'item_id': default_item_id,
                                      'item_size_id': default_item_size_id,
                                      'item_side_id': default_item_side_id,
                                      'bit_code': 'A11',
                                      'flag': 'new'}],
                                    )
        return new_model_df
    def validate_new_row(self, index: QModelIndex) -> bool:
        """
        Needs to be implemented in subclasses
        :param index:
        :return:
        """
        return True
