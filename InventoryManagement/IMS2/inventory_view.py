import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget,
    QLabel, QPushButton, QLineEdit,
    QTableView, QHeaderView, QAbstractItemView,
    QHBoxLayout, QVBoxLayout,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QIcon
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab
from itemview_delegate import ItemViewDelegate


class InventoryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.initializeUI()

    async def initializeUI(self):
        self.setMinimumSize(1400, 800)
        self.setWindowTitle("다나을 재고관리")
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

    def setupItemView(self, item_name=None):
        # items view
        item_view = QTableView(self)
        item_view.horizontalHeader().setStretchLastSection(True)
        item_view.setAlternatingRowColors(True)
        item_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        item_view.resizeColumnsToContents()
        item_view.setSortingEnabled(True)

        self.item_proxy_model = QSortFilterProxyModel()
        self.item_proxy_model.setSourceModel(self.item_model)
        self.item_proxy_model.setFilterKeyColumn(1)
        item_view.setModel(self.item_proxy_model)

        delegate = ItemViewDelegate(self)
        item_view.setItemDelegateForColumn(2, delegate)

        item_widget = QWidget(self)
        self.item_search_bar = QLineEdit(self)
        self.item_search_bar.setPlaceholderText('품목명 입력')
        self.item_search_bar.textChanged.connect(self.item_proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        del_item_btn = QPushButton('삭제')
        mod_item_btn = QPushButton('변경')

        item_hbox = QHBoxLayout()
        item_hbox.addWidget(self.item_search_bar)
        item_hbox.addStretch(1)
        item_hbox.addWidget(add_item_btn)
        item_hbox.addWidget(del_item_btn)
        item_hbox.addWidget(mod_item_btn)

        item_vbox = QVBoxLayout()
        item_vbox.addLayout(item_hbox)
        item_vbox.addWidget(item_view)
        item_widget.setLayout(item_vbox)

        item_widget.setMaximumWidth(500)

        item_dock_widget = QDockWidget('품목', self)
        item_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        item_dock_widget.setWidget(item_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, item_dock_widget)

    def setupSkuView(self):
        # skus view
        sku_view = QTableView(self)
        sku_view.horizontalHeader().setStretchLastSection(True)
        sku_view.setAlternatingRowColors(True)
        sku_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        sku_view.resizeColumnsToContents()
        sku_view.setSortingEnabled(True)

        self.sku_proxy_model = QSortFilterProxyModel()
        self.sku_proxy_model.setSourceModel(self.sku_model)
        self.sku_proxy_model.setFilterKeyColumn(1)
        self.item_search_bar.textChanged.connect(self.sku_proxy_model.setFilterFixedString)
        sku_view.setModel(self.sku_proxy_model)

        sku_widget = QWidget(self)
        add_sku_btn = QPushButton('추가')
        del_sku_btn = QPushButton('삭제')
        mod_sku_btn = QPushButton('변경')

        sku_hbox = QHBoxLayout()
        sku_hbox.addStretch(1)
        sku_hbox.addWidget(add_sku_btn)
        sku_hbox.addWidget(del_sku_btn)
        sku_hbox.addWidget(mod_sku_btn)

        sku_vbox = QVBoxLayout()
        sku_vbox.addLayout(sku_hbox)
        sku_vbox.addWidget(sku_view)
        sku_widget.setLayout(sku_vbox)

        sku_dock_widget = QDockWidget('세부품목', self)
        sku_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                        Qt.RightDockWidgetArea)
        sku_dock_widget.setWidget(sku_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, sku_dock_widget)

    def setupTransactionView(self):
        # transaction view
        tr_view = QTableView(self)
        tr_view.horizontalHeader().setStretchLastSection(True)
        tr_view.setAlternatingRowColors(True)
        tr_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        tr_view.resizeColumnsToContents()
        tr_view.setSortingEnabled(True)

        self.tr_proxy_model = QSortFilterProxyModel(self.tr_model)
        self.tr_proxy_model.setSourceModel(self.tr_model)
        tr_view.setModel(self.tr_proxy_model)
        tr_widget = QWidget(self)

        buy_btn = QPushButton('매입')
        sell_btn = QPushButton('매도')
        modify_btn = QPushButton('매매수정')
        delete_btn = QPushButton('매매삭제')
        adjust_plus_btn = QPushButton('조정+')
        adjust_minus_btn = QPushButton('조정-')

        tr_hbox = QHBoxLayout()
        tr_hbox.addWidget(buy_btn)
        tr_hbox.addWidget(sell_btn)
        tr_hbox.addStretch(1)
        tr_hbox.addWidget(modify_btn)
        tr_hbox.addWidget(delete_btn)
        tr_hbox.addStretch(1)
        tr_hbox.addWidget(adjust_plus_btn)
        tr_hbox.addWidget(adjust_minus_btn)
        tr_hbox.addStretch(10)

        tr_vbox = QVBoxLayout()
        tr_vbox.addLayout(tr_hbox)
        tr_vbox.addWidget(tr_view)

        tr_widget.setLayout(tr_vbox)
        self.setCentralWidget(tr_widget)

    def setUpMainWindow(self):
        self.setupItemView()
        self.setupSkuView()
        self.setupTransactionView()


async def main():
    app = QApplication(sys.argv)
    ex = InventoryWindow()
    await ex.initializeUI()
    app.exec()


if __name__ == '__main__':
    asyncio.run(main())
