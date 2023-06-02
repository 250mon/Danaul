import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QComboBox,
    QTableView, QHeaderView, QAbstractItemView,
    QHBoxLayout, QVBoxLayout,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab


class InventoryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.initializeUI()

    async def initializeUI(self):
        self.setMinimumSize(1000, 600)
        self.setWindowTitle("Danaul Inventory - Items")
        await self.createModel()
        self.setUpMainWindow()
        self.show()

    async def createModel(self):
        inventory_db = InventoryDb('db_settings')
        lab = await Lab(inventory_db)

        # get raw data from db
        tables = ['items', 'skus', 'transactions']
        get_dfs = [lab.get_df_from_db(table) for table in tables]
        dfs_from_db = await asyncio.gather(*get_dfs)
        items_df, skus_df, trs_df = dfs_from_db

        # make model data
        items_df['category'] = items_df['category_id'].map(lab.categories)
        items_model_data = items_df.drop(['category_id'], axis=1)
        self.item_model = PandasModel(items_model_data)

        i_s = items_df.set_index('item_id')['item_name']
        skus_df['item_name'] = skus_df['item_id'].map(i_s)
        skus_df['item_size'] = skus_df['item_size_id'].map(lab.item_sizes)
        skus_df['item_side'] = skus_df['item_side_id'].map(lab.item_sides)
        skus_model_data = skus_df.drop(['item_id', 'item_size_id', 'item_side_id'], axis=1)
        self.sku_model = PandasModel(skus_model_data)

        s_df = skus_df.set_index('sku_id')
        trs_df['item_name'] = trs_df['sku_id'].map(s_df['item_name'])
        trs_df['item_size'] = trs_df['sku_id'].map(s_df['item_size'])
        trs_df['item_side'] = trs_df['sku_id'].map(s_df['item_side'])
        trs_df['tr_type'] = trs_df['tr_type_id'].map(lab.tr_types)
        trs_df['user_name'] = trs_df['user_id'].map(lab.users)
        trs_model_data = trs_df.drop(['sku_id', 'tr_type_id', 'user_id'], axis=1)
        self.tr_model = PandasModel(trs_model_data)

    def setUpMainWindow(self):
        item_view = QTableView(self)
        item_view.resize(800, 500)
        item_view.horizontalHeader().setStretchLastSection(True)
        item_view.setAlternatingRowColors(True)
        item_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        item_view.setModel(self.item_model)

        sku_view = QTableView(self)
        sku_view.resize(800, 500)
        sku_view.horizontalHeader().setStretchLastSection(True)
        sku_view.setAlternatingRowColors(True)
        sku_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        sku_view.setModel(self.sku_model)

        tr_view = QTableView(self)
        tr_view.resize(800, 500)
        tr_view.horizontalHeader().setStretchLastSection(True)
        tr_view.setAlternatingRowColors(True)
        tr_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        tr_view.setModel(self.tr_model)

        main_layout = QVBoxLayout()
        main_layout.addWidget(item_view)
        main_layout.addWidget(sku_view)
        main_layout.addWidget(tr_view)
        self.setLayout(main_layout)

async def main():
    app = QApplication(sys.argv)
    ex = InventoryWindow()
    await ex.initializeUI()
    app.exec()


if __name__ == '__main__':
    asyncio.run(main())
