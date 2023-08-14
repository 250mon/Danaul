import os
import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex
from di_data_model import DataModel
from di_lab import Lab
from di_logger import Logs, logging
from constants import EditLevel
from datetime_utils import *
from sku_model import SkuModel
from constants import RowFlags

logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""


class TrModel(DataModel):
    def __init__(self, user_name: str, sku_model: SkuModel):
        self.sku_model = sku_model
        self.init_params()
        self.selected_upper_name = None
        self.update_skus_params()
        # setting a model is carried out in the DataModel
        super().__init__(user_name)

    def init_params(self):
        self.set_table_name('transactions')

        self.col_edit_lvl = {
            'tr_id': EditLevel.NotEditable,
            'sku_id': EditLevel.NotEditable,
            'tr_type': EditLevel.Creatable,
            'tr_qty': EditLevel.Creatable,
            'before_qty': EditLevel.NotEditable,
            'after_qty': EditLevel.NotEditable,
            'tr_timestamp': EditLevel.Creatable,
            'description': EditLevel.UserModifiable,
            'user_name': EditLevel.Creatable,
            'tr_type_id': EditLevel.NotEditable,
            'user_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

    def set_upper_model_index(self, sku_model_index: QModelIndex or None):
        self.selected_upper_index = sku_model_index

        if sku_model_index is not None:
            self.selected_upper_id = sku_model_index.siblingAtColumn(
                self.sku_model.get_col_number('sku_id')).data()
            self.selected_upper_name = sku_model_index.siblingAtColumn(
                self.sku_model.get_col_number('sku_name')).data()
        else:
            self.selected_upper_id = None
            self.selected_upper_name = None

    def update_skus_params(self):
        skus_df = Lab().table_df['skus'].loc[:, ['sku_id', 'active', 'bit_code', 'sku_qty']]
        skus_df_id_indexed = skus_df.set_index('sku_id')
        self.sku_active_s: pd.Series = skus_df_id_indexed.iloc[:, 0]
        self.sku_bitcode_s: pd.Series = skus_df_id_indexed.iloc[:, 1]
        self.sku_qty_s: pd.Series = skus_df_id_indexed.iloc[:, 2]

    async def update(self):
        await super().update()

    def set_add_on_cols(self):
        """
        Needs to be implemented in the subclasses
        Adds extra columns of each name mapped to ids of supplementary data
        :return:
        """
        # set more columns for the view
        self.model_df['tr_type'] = self.model_df['tr_type_id'].map(Lab().tr_type_s)
        self.model_df['user_name'] = self.model_df['user_id'].map(Lab().user_name_s)
        self.model_df['flag'] = RowFlags.OriginalRow

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in ['description']]
        return default_info_list

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
            int_type_columns = ['tr_id', 'user_id', 'sku_id', 'tr_type_id',
                                'tr_qty', 'before_qty', 'after_qty']
            if col_name in int_type_columns:
                # if column data is int, return int type
                return int(data_to_display)
            elif col_name == 'tr_timestamp':
                # data type is datetime.date
                return pydt_to_qdt(data_to_display)
            else:
                # otherwise, string type
                return str(data_to_display)

        elif role == Qt.TextAlignmentRole:
            left_aligned = ['description']
            if col_name in left_aligned:
                return Qt.AlignLeft
            else:
                return Qt.AlignCenter

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
        if col_name == 'tr_type':
            id_col = self.get_col_number('tr_type_id')
            self.model_df.iloc[index.row(), id_col] = Lab().tr_type_id_s.loc[value]
        elif col_name == 'tr_timestamp':
            # data type is datetime.date
            if isinstance(value, QDateTime):
                value = qdt_to_pydt(value)

        return super().setData(index, value, role)

    def make_a_new_row_df(self, next_new_id, **kwargs) -> pd.DataFrame or None:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise None
        """
        if self.selected_upper_id is None:
            logger.error('make_a_new_row_df: sku_id is empty')
            return None
        elif not self.sku_active_s[self.selected_upper_id]:
            logger.error('make_a_new_row_df: sku_id is not active')
            return None

        sku_qty = self.sku_qty_s.loc[self.selected_upper_id]
        tr_type = kwargs['tr_type']
        tr_type_id = Lab().tr_type_id_s.loc[tr_type]
        user_id = Lab().user_id_s.loc[self.user_name]

        new_model_df = pd.DataFrame([{
            'tr_id': next_new_id,
            'sku_id': self.selected_upper_id,
            'tr_type': tr_type,
            'tr_qty': 0,
            'before_qty': sku_qty,
            'after_qty': sku_qty,
            'tr_timestamp': datetime.now(),
            'description': "",
            'user_name': self.user_name,
            'user_id': user_id,
            'tr_type_id': tr_type_id,
            'flag': RowFlags.NewRow
        }])
        return new_model_df

    def validate_new_row(self, index: QModelIndex) -> bool:
        """
        This is used to validate a new row generated by SingleTrWindow
        when the window is done with creating a new row and emits create_tr_signal
        :param index:
        :return:
        """
        sku_id = index.siblingAtColumn(self.get_col_number('sku_id')).data()
        tr_type = index.siblingAtColumn(self.get_col_number('tr_type')).data()
        tr_qty = index.siblingAtColumn(self.get_col_number('tr_qty')).data()
        before_qty = index.siblingAtColumn(self.get_col_number('before_qty')).data()

        result = True
        if tr_type == "Buy":
            self.plus_qty_to_models('+', before_qty, tr_qty, index)
        elif tr_type == "Sell":
            if tr_qty > before_qty:
                result = False
            else:
                self.plus_qty_to_models('-', before_qty, tr_qty, index)
        elif tr_type == "AdjustmentPlus":
            self.plus_qty_to_models('+', before_qty, tr_qty, index)
        elif tr_type == "AdjustmentMinus":
            if tr_qty > before_qty:
                result = False
            else:
                self.plus_qty_to_models('-', before_qty, tr_qty, index)

        debug_msg = "valid" if result is True else "not valid"
        logger.debug(f"validate_new_tr: Sku({sku_id}) Tr({tr_type}) is {debug_msg}")

        return result

    def plus_qty_to_models(self, op, before_qty, tr_qty, index):
        if op == '+':
            after_qty = before_qty + tr_qty
        elif op == '-':
            after_qty = before_qty - tr_qty

        before_qty_idx = index.siblingAtColumn(self.get_col_number('before_qty'))
        self.setData(before_qty_idx, after_qty)
        after_qty_idx = index.siblingAtColumn(self.get_col_number('after_qty'))
        self.setData(after_qty_idx, after_qty)
        self.sku_model.update_sku_qty_after_transaction(self.selected_upper_index, after_qty)
        logger.debug(f'validate_new_row: before_qty {before_qty}, tr_qty {tr_qty} => after_qty {after_qty}')
