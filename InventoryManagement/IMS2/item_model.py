import os
import pandas as pd
from PySide6.QtCore import Qt, QModelIndex
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class ItemModel(PandasModel):
    def __init__(self):
        super().__init__()
        # getting item data from db
        self.lab = Lab(InventoryDb('db_settings'))

        # need category_id to category_name mapping table
        self.category_df: pd.DataFrame = self.lab.categories_df

        # set data to model
        # mapping table where the actual column is located in the table
        self.column_headers = ['item_id', 'item_valid', 'item_name',
                               'category_name', 'description', 'modification']

        self.model_df = None
        self.set_model_df()

        # for later use
        self.tmp_df = None
        self.mod_start_idx = -1
        self.mod_end_idx = -1

    def set_model_df(self):
        # for category name mapping
        cat_df = self.category_df.set_index('category_id')
        cat_s: pd.Series = cat_df['category_name']

        self.model_df = self.lab.items_df
        self.model_df['category_name'] = self.model_df['category_id'].map(cat_s)
        self.model_df['modification_category'] = None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole) -> str or None:
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        def get_data(r_idx, c_idx):
            col_series = self.model_df[self.column_headers[c_idx]]
            data = col_series.iat[r_idx]
            return data

        is_deleted = get_data(index.row(), self.column_headers.index('modification')) == 'deleted'
        if is_deleted:
            return None

        data_to_display = get_data(index.row(), index.column())
        if data_to_display is None:
            return None

        if role == Qt.DisplayRole:
            return str(data_to_display)
        elif role == Qt.EditRole:
            return str(data_to_display)

        return None

    def setData(self,
                index: QModelIndex,
                value: str,
                role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            # taking care of converting str type input to bool type
            if index.column() == self.column_headers.index('item_valid'):
                val: bool = False
                if value == 'True':
                    val = True
            else:
                val: object = value
            return super().setData(index, val, role)
        return False


    def add_template_row(self):
        new_df = pd.DataFrame([(-1, True, "", 1, "", self.category_df.iat[0, 1], 'new')],
                              columns=self.model_df.columns)
        self.model_df = pd.concat([self.model_df, new_df])

    def del_template_row(self):
        self.model_df.drop([-1])

    async def update_db(self):
        pass

        # update model_df
        await Lab().update_lab_df_from_db('items')
        self.set_model_df()
        return result

    def prepare_modified_rows_to_update(self, start_idx, end_idx):
        self.mod_start_idx = start_idx
        self.mod_end_idx = end_idx