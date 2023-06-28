import os
import pandas as pd
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
        self.db_df = self.lab.items_df

        # column names that will be appearing in the view
        self.col_names = ['item_id', 'item_valid', 'item_name', 'category', 'description']

        # need category_id to category_name mapping table
        self.categories = None
        self.cat_df: pd.DataFrame = self.lab.categories_df.set_index('category_id')

        # set data to model
        self.set_model_data()

        # for later use
        self.tmp_df = None
        self.mod_start_idx = -1
        self.mod_end_idx = -1

    def set_model_data(self):
        # for category name mapping
        cat_s: pd.Series = self.cat_df['category_name']
        self.categories = cat_s.to_list()
        self.db_df['category'] = self.db_df['category_id'].map(cat_s)

        # the model data for PandasModel is _dataframe
        model_df = self.db_df.fillna("")
        self._dataframe = model_df[self.col_names]

    def add_template_row(self):
        new_df = pd.DataFrame([(-1, True, "", self.categories[0], "")],
                              columns=self.col_names)
        self.tmp_df = self._dataframe
        self._dataframe = pd.concat([self._dataframe, new_df])

    def del_template_row(self):
        if self.tmp_df is not None:
            self._dataframe = self.tmp_df
            self.tmp_df = None

    def prepare_modified_rows_to_update(self, start_idx, end_idx):
        self.mod_start_idx = start_idx
        self.mod_end_idx = end_idx

    def get_added_new_row(self):
        new_items_df = self._dataframe.iloc[-1, :]

        # ['item_id', 'item_valid', 'item_name', 'category', 'description']
        # ['item_id', 'item_valid', 'item_name', 'category_id', 'description']

        # new_items_df = pd.DataFrame([[None, True, 'n5', 2, 'lala'],
        #                              [None, True, 'n6', 3, 'lolo']],
        #                             columns=['item_id', 'item_valid', 'item_name',
        #                                      'category_id', 'description'])
        logger.debug('Adding a new item ...')
        logger.debug(new_items_df)
        return new_items_df

    def get_modified_rows(self):
        modified_items_df = self._dataframe.iloc[self.mod_start_idx: self.mod_end_idx, :]
        logger.debug('Modifying items ...')
        logger.debug(modified_items_df)

        # reset idxes
        self.mod_start_idx = -1
        self.mod_end_idx = -1

        return modified_items_df