import sys, os
import asyncio
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget,
    QPushButton, QLineEdit, QTableView, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel
from pandas_model import PandasModel
from async_helper import AsyncHelper
from item_model import ItemModel
from di_db import InventoryDb
from di_lab import Lab
from di_logger import Logs, logging
from combobox_delegate import ComboBoxDelegate
from single_item_window import SingleItemWindow


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class InventoryWindow(QMainWindow):
    start_signal = Signal(str, pd.DataFrame)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()

        self.initializeUI()

    def initializeUI(self):
        self.setMinimumSize(1400, 800)
        self.setWindowTitle("다나을 재고관리")
        self.item_model = ItemModel()

        self.setUpMainWindow()
        self.show()

    # async def createModel(self):
    #     self.lab = Lab(InventoryDb('db_settings'))
    #     # get raw data from db
    #     tables = ['skus', 'transactions']
    #     get_dfs = [self.lab.get_df_from_db(table) for table in tables]
    #     dfs_from_db = await asyncio.gather(*get_dfs)
    #     skus_df, trs_df = dfs_from_db
    #
    #     # make model data
    #
    #     i_s = self.lab.items_df.set_index('item_id')['item_name']
    #     skus_df['item_name'] = skus_df['item_id'].map(i_s)
    #     skus_df['item_size'] = skus_df['item_size_id'].map(self.lab.item_sizes)
    #     skus_df['item_side'] = skus_df['item_side_id'].map(self.lab.item_sides)
    #     skus_df.fillna("", inplace=True)
    #     # skus_model_data_df = skus_df.drop(['item_id', 'item_size_id', 'item_side_id'], axis=1)
    #     skus_model_data_df = skus_df[['sku_id', 'item_name', 'item_size', 'item_side',
    #                                  'sku_qty', 'min_qty', 'expiration_date', 'bit_code',
    #                                  'description']]
    #     self.sku_model = PandasModel(skus_model_data_df)
    #
    #     s_df = skus_df.set_index('sku_id')
    #     trs_df['item_name'] = trs_df['sku_id'].map(s_df['item_name'])
    #     trs_df['item_size'] = trs_df['sku_id'].map(s_df['item_size'])
    #     trs_df['item_side'] = trs_df['sku_id'].map(s_df['item_side'])
    #     trs_df['tr_type'] = trs_df['tr_type_id'].map(self.lab.tr_types)
    #     trs_df['user_name'] = trs_df['user_id'].map(self.lab.users)
    #     trs_df.fillna("", inplace=True)
    #     # trs_model_data_df = trs_df.drop(['sku_id', 'tr_type_id', 'user_id'], axis=1)
    #     trs_model_data_df = trs_df[['tr_id', 'tr_type', 'item_name', 'item_size',
    #                                 'item_side', 'tr_qty', 'before_qty', 'after_qty',
    #                                 'tr_timestamp', 'description']]
    #     self.tr_model = PandasModel(trs_model_data_df)

    def setupItemView(self):
        # items view

        self.item_view = QTableView(self)
        self.item_view.horizontalHeader().setStretchLastSection(True)
        self.item_view.setAlternatingRowColors(True)
        # item_view.setSelectionMode(
        #     QAbstractItemView.SelectionMode.ExtendedSelection
        # )

        self.item_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.item_view.resizeColumnsToContents()
        self.item_view.setSortingEnabled(True)

        self.item_proxy_model = QSortFilterProxyModel()
        self.item_proxy_model.setSourceModel(self.item_model)
        self.item_proxy_model.setFilterKeyColumn(1)
        self.item_view.setModel(self.item_proxy_model)

        # editable columns: category and description
        # a line edit is used as a default delegate
        editable_col_idx = [self.item_model.col_names.index(val)
                            for val in ['category_name', 'description']]
        self.item_model.set_editable_cols(editable_col_idx)
        # for category col, combobox delegate is used
        category_name_list = Lab().categories_df['category_name'].values.tolist()
        delegate = ComboBoxDelegate(category_name_list, self)
        self.item_view.setItemDelegateForColumn(editable_col_idx[0], delegate)

        item_widget = QWidget(self)
        self.item_search_bar = QLineEdit(self)
        self.item_search_bar.setPlaceholderText('품목명 입력')
        self.item_search_bar.textChanged.connect(
            self.item_proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        add_item_btn.clicked.connect(lambda: self.do_actions("add_item"))
        mod_item_btn = QPushButton('수정')
        mod_item_btn.clicked.connect(lambda: self.do_actions("mod_item"))
        del_item_btn = QPushButton('삭제')
        del_item_btn.clicked.connect(lambda: self.do_actions("del_item"))
        save_item_btn = QPushButton('저장')
        save_item_btn.clicked.connect(lambda: self.async_start("save"))

        item_hbox = QHBoxLayout()
        item_hbox.addWidget(self.item_search_bar)
        item_hbox.addStretch(1)
        item_hbox.addWidget(add_item_btn)
        item_hbox.addWidget(mod_item_btn)
        item_hbox.addWidget(del_item_btn)
        item_hbox.addWidget(save_item_btn)

        item_vbox = QVBoxLayout()
        item_vbox.addLayout(item_hbox)
        item_vbox.addWidget(self.item_view)
        item_widget.setLayout(item_vbox)

        item_widget.setMaximumWidth(500)

        item_dock_widget = QDockWidget('품목', self)
        item_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        item_dock_widget.setWidget(item_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, item_dock_widget)

    @Slot(str, pd.DataFrame)
    def do_actions(self, action: str, df: pd.DataFrame = None):
        logger.debug(f'{action}')
        if action == "add_item":
            logger.debug('Adding item ...')
            self.item_model.add_template_row()
            self.item_window = SingleItemWindow(self.item_model)
            # trigger refresh
            # This signal is emitted just before the layout of a model is changed.
            # Components connected to this signal use it to adapt to changes in the model’s layout.
            self.item_model.layoutAboutToBeChanged.emit()
            self.item_model.layoutChanged.emit()
        elif action == "mod_item":
            logger.debug('Modifying item ...')
            selected_indexes = self.item_view.selectedIndexes()
            check_indexes = [idx.isValid() for idx in selected_indexes]
            if len(selected_indexes) > 0 and check_indexes[0] and check_indexes[-1]:
                self.item_window = SingleItemWindow(self.item_model,
                                                    selected_indexes)
                self.item_model.layoutAboutToBeChanged.emit()
                self.item_model.layoutChanged.emit()


    @Slot(str, pd.DataFrame)
    def async_start(self, action: str, df: pd.DataFrame = None):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.update_df(action, df)
        self.start_signal.emit(action, df)


    async def update_df(self, action: str, df: pd.DataFrame = None):
        logger.debug(f'{action}')
        if action == "save":
            logger.debug('Saving ...')
            await self.item_model.update_db()
            # logger.info(results)

        # if action == "add_item":
        #     logger.debug('Adding item ...')
        #     self.item_model.add_template_row()
        #     self.item_window = SingleItemWindow(self.item_model)
        #     # trigger refresh
        #     # This signal is emitted just before the layout of a model is changed.
        #     # Components connected to this signal use it to adapt to changes in the model’s layout.
        #     self.item_model.layoutAboutToBeChanged.emit()
        #     self.item_model.layoutChanged.emit()
        #     self.item_model.get_added_new_row()
        #     # results = await self.lab.di_db.insert_items_df(
        #     #     self.item_model.get_added_new_row())
        #     # logger.info(results)
        # elif action == "mod_item":
        #     logger.debug('Modifying item ...')
        #     selected_indexes = self.item_view.selectedIndexes()
        #     check_indexes = [idx.isValid() for idx in selected_indexes]
        #     if len(selected_indexes) > 0 and check_indexes[0] and check_indexes[-1]:
        #         self.item_window = SingleItemWindow(self.item_model,
        #                                             selected_indexes)
        #         self.item_model.get_modified_rows()

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
        # self.item_search_bar.textChanged.connect(self.sku_proxy_model.setFilterFixedString)
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
        # self.setupSkuView()
        # self.setupTransactionView()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = InventoryWindow()
    async_helper = AsyncHelper(main_window, main_window.update_df)

    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()
