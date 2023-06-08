import asyncio
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
        self.set_model_data()

    def set_model_data(self):
        # for category name mapping
        cat_df = self.lab.categories_df.set_index('category_id')
        cat_s = cat_df['category_name']
        self.db_df['category'] = self.db_df['category_id'].map(cat_s)

        # the model data for PandasModel is _dataframe
        model_df = self.db_df.fillna("")
        self._dataframe = model_df[['item_id', 'item_name', 'category', 'description']]