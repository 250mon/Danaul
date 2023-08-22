import os
import pandas as pd
from typing import Dict, List
from PySide6.QtCore import Qt, QModelIndex, QDate
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
        self.selected_upper_id = None
        self.selected_upper_name = None
        self.beg_timestamp = QDate.currentDate().addMonths(-6)
        self.end_timestamp = QDate.currentDate()
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
            'tr_timestamp': EditLevel.NotEditable,
            'description': EditLevel.UserModifiable,
            'user_name': EditLevel.NotEditable,
            'tr_type_id': EditLevel.NotEditable,
            'user_id': EditLevel.NotEditable,
            'flag': EditLevel.NotEditable
        }

        self.set_column_names(list(self.col_edit_lvl.keys()))
        self.set_column_index_edit_level(self.col_edit_lvl)

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

        logger.debug(f"set_upper_model_index: sku_id({self.selected_upper_id}) is set")

    def set_beg_timestamp(self, beg: QDate):
        self.beg_timestamp = beg
        logger.debug(f"set_beg_timestamp: {self.beg_timestamp}")

    def set_end_timestamp(self, end: QDate):
        self.end_timestamp = end
        logger.debug(f"set_end_timestamp: {self.end_timestamp}")

    async def update(self):
        """
        Override method to use selected_sku_id and begin_/end_ timestamp
        :return:
        """
        # end day needs to be added 1 day otherwise query results only includes those thata
        # were created until the day 00h 00mm 00sec
        logger.debug(f'update: downloading data from DB')
        kwargs = {'sku_id': self.selected_upper_id,
                  'beg_timestamp': self.beg_timestamp.toString("yyyy-MM-dd"),
                  'end_timestamp': self.end_timestamp.addDays(1).toString("yyyy-MM-dd")}
        logger.debug(f'update: {kwargs}')
        await Lab().update_lab_df_from_db(self.table_name, **kwargs)

        self._set_model_df()
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def get_default_delegate_info(self) -> List[int]:
        """
        Returns a list of column indexes for default delegate
        :return:
        """
        default_info_list = [self.get_col_number(c) for c in ['description']]
        return default_info_list

    def get_combobox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the combobox
        for combobox delegate
        :return:
        """
        combo_info_dict = {
            self.get_col_number('tr_type'): Lab().tr_type_s.to_list()
        }
        return combo_info_dict

    def get_spinbox_delegate_info(self) -> Dict[int, List]:
        """
        Returns a dictionary of column indexes and val lists of the spinbox
        for spinbox delegate
        :return:
        """
        spin_info_dict = {
            self.get_col_number('tr_qty'): [1, 1000],
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

    def get_last_row_qty(self):
        if self.model_df.empty:
            last_row = 0
            last_row_qty = 0
        else:
            grp = self.model_df.groupby('sku_id')[['tr_id', 'after_qty']].get_group(self.selected_upper_id)
            grp_sorted = grp.sort_values(['tr_id'], ascending=False)
            last_row = grp_sorted['tr_id'].head(1).item()
            last_row_qty = grp_sorted['after_qty'].head(1).item()
        logger.debug(f'get_last_row_qty: last_row {last_row}, last_row_qty {last_row_qty}')
        return last_row_qty

    def make_a_new_row_df(self, next_new_id, **kwargs) -> pd.DataFrame or None:
        """
        Needs to be implemented in subclasses
        :param next_new_id:
        :return: new dataframe if succeeds, otherwise None
        """
        logger.debug(f"make_a_new_row_df: new_id({next_new_id})\n")
        if self.selected_upper_id is None:
            logger.error('make_a_new_row_df: sku_id is empty')
            return None
        elif not self.sku_model.get_data_from_id(self.selected_upper_id, 'active'):
            logger.error('make_a_new_row_df: sku_id is not active')
            return None

        last_qty = self.get_last_row_qty()
        tr_type = kwargs['tr_type']
        tr_type_id = Lab().tr_type_id_s.loc[tr_type]
        user_id = Lab().user_id_s.loc[self.user_name]

        new_model_df = pd.DataFrame([{
            'tr_id': next_new_id,
            'sku_id': self.selected_upper_id,
            'tr_type': tr_type,
            'tr_qty': 1,
            'before_qty': last_qty,
            'after_qty': last_qty + 1,
            'tr_timestamp': datetime.now(),
            'description': "",
            'user_name': self.user_name,
            'user_id': user_id,
            'tr_type_id': tr_type_id,
            'flag': RowFlags.NewRow
        }])
        return new_model_df

    def make_a_new_row_df_from_bit_code(self, bit_df: pd.DataFrame):
        sku_sub_df = self.sku_model.model_df.loc[:, ["sku_id", "bit_code"]]
        sku_bit_id_df = sku_sub_df.set_index("bit_code")
        joined_df = pd.merge(bit_df, sku_bit_id_df, left_index=True, right_index=True)
        logger.debug(f"make_a_new_row_df_from_bit_code:\n"
                     f"{joined_df}")

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

        if tr_qty <= 0:
            logger.debug(f"validate_new_row: tr_qty is not positive integer {tr_qty}")
            return False

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
        # not allow a user to change tr_qty after this point
        self.clear_new_rows()

        return result

    def plus_qty_to_models(self, op, before_qty, tr_qty, index):
        after_qty = 0
        if op == '+':
            after_qty = before_qty + tr_qty
        elif op == '-':
            after_qty = before_qty - tr_qty

        after_qty_idx = index.siblingAtColumn(self.get_col_number('after_qty'))
        self.setData(after_qty_idx, after_qty)
        logger.debug(f'validate_new_row: before_qty {before_qty}, tr_qty {tr_qty} => after_qty {after_qty}')

    def update_sku_qty(self):
        last_qty = self.get_last_row_qty()
        self.sku_model.update_sku_qty_after_transaction(self.selected_upper_index, last_qty)
