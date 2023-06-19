import asyncio
import pandas as pd
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab


"""
Handling a raw dataframe from db to convert into model data(dataframe)
Also, converting model data(dataframe) back into a data class to update db
"""
class ItemModel(PandasModel):
    def __init__(self):
        super().__init__()
        self.lab = Lab(InventoryDb('db_settings'))
        self.db_df = self.lab.items_df

        # lists of etc(reference data)
        self.categories = None

        # column names that will be appearing in the view
        self.col_names = ['item_id', 'item_valid', 'item_name', 'category', 'description']

        # set data to model
        self.set_model_data()

    def set_model_data(self):
        # for category name mapping
        cat_df: pd.DataFrame = self.lab.categories_df.set_index('category_id')
        cat_s: pd.Series = cat_df['category_name']
        self.categories = cat_s.to_list()
        self.db_df['category'] = self.db_df['category_id'].map(cat_s)

        # the model data for PandasModel is _dataframe
        model_df = self.db_df.fillna("")
        self._dataframe = model_df[self.col_names]

    def add_new_row(self):
        new_df = pd.DataFrame([(-1, True, "", self.categories[0], "")],
                              columns=self.col_names)
        self._dataframe = pd.concat([self._dataframe, new_df])

    def get_changes(self):
        new_items_df = pd.DataFrame([[None, True, 'n5', 2, 'lala'],
                                     [None, True, 'n6', 3, 'lolo']],
                                    columns=['item_id', 'item_valid', 'item_name',
                                             'category_id', 'description'])
        return new_items_df

