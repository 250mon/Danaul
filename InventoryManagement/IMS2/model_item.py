import asyncio
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab


"""
Handling a raw dataframe from db to convert into model data
Also, converting model data back into a data class to update db
"""
class ItemModel(PandasModel):
    def __init__(self):
        super().__init__()

    def get_model(self):
        inventory_db = InventoryDb('db_settings')
        lab = await Lab(inventory_db)

        # make model data

        lab.items_df['category'] = lab.items_df['category_id'].map(lab.categories_df)
        items_df.fillna("", inplace=True)
        # items_model_data_df = items_df.drop(['category_id'], axis=1)
        items_model_data_df = items_df[['item_id', 'item_name', 'category', 'description']]
        self.item_model = PandasModel(items_model_data_df)

        i_s = items_df.set_index('item_id')['item_name']
        skus_df['item_name'] = skus_df['item_id'].map(i_s)
        skus_df['item_size'] = skus_df['item_size_id'].map(lab.item_sizes)
        skus_df['item_side'] = skus_df['item_side_id'].map(lab.item_sides)
        skus_df.fillna("", inplace=True)
        # skus_model_data_df = skus_df.drop(['item_id', 'item_size_id', 'item_side_id'], axis=1)
        skus_model_data_df = skus_df[['sku_id', 'item_name', 'item_size', 'item_side',
                                      'sku_qty', 'min_qty', 'expiration_date', 'bit_code',
                                      'description']]
        self.sku_model = PandasModel(skus_model_data_df)

        s_df = skus_df.set_index('sku_id')
        trs_df['item_name'] = trs_df['sku_id'].map(s_df['item_name'])
        trs_df['item_size'] = trs_df['sku_id'].map(s_df['item_size'])
        trs_df['item_side'] = trs_df['sku_id'].map(s_df['item_side'])
        trs_df['tr_type'] = trs_df['tr_type_id'].map(lab.tr_types)
        trs_df['user_name'] = trs_df['user_id'].map(lab.users)
        trs_df.fillna("", inplace=True)
        # trs_model_data_df = trs_df.drop(['sku_id', 'tr_type_id', 'user_id'], axis=1)
        trs_model_data_df = trs_df[['tr_id', 'tr_type', 'item_name', 'item_size',
                                    'item_side', 'tr_qty', 'before_qty', 'after_qty',
                                    'tr_timestamp', 'description']]
        self.tr_model = PandasModel(trs_model_data_df)
