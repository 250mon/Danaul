import sys
import asyncio
import signal

import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget,
    QLabel, QPushButton, QLineEdit,
    QTableView, QHeaderView, QAbstractItemView,
    QHBoxLayout, QVBoxLayout,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QObject, Signal, Slot, QEvent, QSortFilterProxyModel
)
from PySide6.QtGui import QIcon
from pandas_model import PandasModel
from model_item import ItemModel
from di_db import InventoryDb
from di_lab import Lab
from di_logger import Logs, logging
from itemview_delegate import ItemViewDelegate
from item_widget_mapper import ItemWidget


logger = Logs().get_logger('inventory_view')
logger.setLevel(logging.DEBUG)

class AsyncHelper(QObject):

    class ReenterQtObject(QObject):
        """ This is a QObject to which an event will be posted, allowing
            asyncio to resume when the event is handled. event.fn() is
            the next entry point of the asyncio event loop. """
        def event(self, event: QEvent):
            if event.type() == QEvent.Type.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        """ This is the QEvent that will be handled by the ReenterQtObject.
            self.fn is the next entry point of the asyncio event loop. """
        def __init__(self, fn):
            super().__init__(QEvent.Type(QEvent.Type.User + 1))
            self.fn = fn

    def __init__(self, worker, entry):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry
        self.loop = asyncio.new_event_loop()
        self.done = {}

        self.worker = worker
        if hasattr(self.worker, "start_signal") and isinstance(self.worker.start_signal, Signal):
            self.worker.start_signal.connect(self.on_worker_started)
        if hasattr(self.worker, "done_signal") and isinstance(self.worker.done_signal, Signal):
            self.worker.done_signal.connect(self.on_worker_done)

    @Slot(str, pd.DataFrame)
    def on_worker_started(self, action: str, df: pd.DataFrame):
        """ To use asyncio and Qt together, one must run the asyncio
            event loop as a "guest" inside the Qt "host" event loop. """
        logger.debug(f'on_worker_started... {action}')
        if not self.entry:
            raise Exception("No entry point for the asyncio event loop was set.")
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.entry(action, df))
        self.loop.call_soon(lambda: self.next_guest_run_schedule(action))
        self.done[action] = False  # Set this explicitly as we might want to restart the guest run.
        self.loop.run_forever()

    @Slot(str)
    def on_worker_done(self, action: str):
        """ When all our current asyncio tasks are finished, we must end
            the "guest run" lest we enter a quasi idle loop of switching
            back and forth between the asyncio and Qt loops. We can
            launch a new guest run by calling launch_guest_run() again. """
        self.done[action] = True

    def continue_loop(self, action: str):
        """ This function is called by an event posted to the Qt event
            loop to continue the asyncio event loop. """
        if not self.done[action]:
            self.loop.call_soon(lambda: self.next_guest_run_schedule(action))
            if not self.loop.is_running():
                self.loop.run_forever()

    def next_guest_run_schedule(self, action: str):
        """ This function serves to pause and re-schedule the guest
            (asyncio) event loop inside the host (Qt) event loop. It is
            registered in asyncio as a callback to be called at the next
            iteration of the event loop. When this function runs, it
            first stops the asyncio event loop, then by posting an event
            on the Qt event loop, it both relinquishes to Qt's event
            loop and also schedules the asyncio event loop to run again.
            Upon handling this event, a function will be called that
            resumes the asyncio event loop. """
        self.loop.stop()
        QApplication.postEvent(self.reenter_qt,
                               self.ReenterQtEvent(lambda: self.continue_loop(action)))


class InventoryWindow(QMainWindow):
    start_signal = Signal(str, pd.DataFrame)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()

        self.initializeUI()

    def initializeUI(self):
        self.setMinimumSize(1400, 800)
        self.setWindowTitle("다나을 재고관리")

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.createModel())
        finally:
            loop.close()

        self.setUpMainWindow()
        self.show()

    async def createModel(self):
        inventory_db = InventoryDb('db_settings')
        self.lab = await Lab(inventory_db)

        self.item_model = ItemModel()

        # get raw data from db
        tables = ['skus', 'transactions']
        get_dfs = [self.lab.get_df_from_db(table) for table in tables]
        dfs_from_db = await asyncio.gather(*get_dfs)
        skus_df, trs_df = dfs_from_db

        # make model data

        i_s = self.lab.items_df.set_index('item_id')['item_name']
        skus_df['item_name'] = skus_df['item_id'].map(i_s)
        skus_df['item_size'] = skus_df['item_size_id'].map(self.lab.item_sizes)
        skus_df['item_side'] = skus_df['item_side_id'].map(self.lab.item_sides)
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
        trs_df['tr_type'] = trs_df['tr_type_id'].map(self.lab.tr_types)
        trs_df['user_name'] = trs_df['user_id'].map(self.lab.users)
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
        # item_view.setSelectionMode(
        #     QAbstractItemView.SelectionMode.ExtendedSelection
        # )

        item_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        item_view.resizeColumnsToContents()
        item_view.setSortingEnabled(True)

        self.item_proxy_model = QSortFilterProxyModel()
        self.item_proxy_model.setSourceModel(self.item_model)
        self.item_proxy_model.setFilterKeyColumn(1)
        item_view.setModel(self.item_proxy_model)

        self.item_model.set_editable_cols([2, 3])
        delegate = ItemViewDelegate(self)
        item_view.setItemDelegateForColumn(2, delegate)

        item_widget = QWidget(self)
        self.item_search_bar = QLineEdit(self)
        self.item_search_bar.setPlaceholderText('품목명 입력')
        self.item_search_bar.textChanged.connect(
            self.item_proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        add_item_btn.clicked.connect(lambda: self.async_start("update_items", None))
        del_item_btn = QPushButton('삭제')
        mod_item_btn = QPushButton('저장')

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

    @Slot(str, pd.DataFrame)
    def async_start(self, action: str, df: pd.DataFrame):
        self.start_signal.emit(action, df)

    async def update_db(self, action: str, df: pd.DataFrame):
        logger.debug(f'{action}')
        if action == "update_items":
            logger.debug('Updating DB ... update_items')
            new_item_widget = ItemWidget(self.item_model)
            logger.debug(self.item_model.get_changes())
            # results = await self.lab.di_db.insert_items_df(
            #     self.item_model.get_changes())
            # logger.info(results)

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
        self.setupSkuView()
        self.setupTransactionView()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = InventoryWindow()
    async_helper = AsyncHelper(main_window, main_window.update_db)

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()
