import sys, os
import pandas as pd
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDockWidget, QMessageBox,
    QPushButton, QLineEdit, QTableView, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel, QModelIndex
from login_widget import LoginWidget
from async_helper import AsyncHelper
from item_model import ItemModel
from di_lab import Lab
from di_db import InventoryDb
from di_logger import Logs, logging
from combobox_delegate import ComboBoxDelegate
from single_item_window import SingleItemWindow
from item_widget import ItemWidget


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

DB_SETTINGS_FILE = 'db_settings'
Lab(InventoryDb(DB_SETTINGS_FILE))

class InventoryWindow(QMainWindow):
    start_signal = Signal(str, pd.DataFrame)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        # self.login()
        self.user_name = None
        self.initializeUI('admin')

    def login(self):
        self.login_widget = LoginWidget(DB_SETTINGS_FILE, self)
        self.login_widget.start_main.connect(self.initializeUI)
        self.login_widget.show()

    @Slot(str)
    def initializeUI(self, user_name: str):
        self.user_name = user_name
        self.setMinimumSize(1400, 800)
        self.setWindowTitle("다나을 재고관리")
        # self.item_model = ItemModel(self.user_name)

        self.setUpMainWindow()

        #
        self. async_helper = AsyncHelper(self, self.save_to_db)

        self.show()

    def setUpMainWindow(self):
        self.item_widget = ItemWidget(self.user_name, self)
        self.item_widget.setMaximumWidth(500)

        item_dock_widget = QDockWidget('품목', self)
        item_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        item_dock_widget.setWidget(self.item_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, item_dock_widget)

        # self.setupItemView()
        # self.setupSkuView()
        # self.setupTransactionView()

    @Slot(str, pd.DataFrame)
    def do_actions(self, action: str, df: pd.DataFrame = None):
        def get_selected_indexes():
            # the indexes of proxy model
            selected_indexes = self.item_view.selectedIndexes()
            check_indexes = [idx.isValid() for idx in selected_indexes]
            if len(selected_indexes) > 0 and False not in check_indexes:
                logger.debug(f'Indexes selected: {selected_indexes}')
                return selected_indexes
            else:
                logger.debug(f'Indexes not selected or invalid: {selected_indexes}')
                return None

        logger.debug(f'{action}')
        if action == "add_item":
            logger.debug('Adding item ...')
            new_item_model = ItemModel(self.user_name, template_flag=True)
            self.new_item_proxy_model.setSourceModel(new_item_model)
            self.item_window = SingleItemWindow(self.new_item_proxy_model)
            # add_item_signal is emitted from the ok button of SingleItemWindow
            # when adding is done
            self.item_window.add_item_signal.connect(self.add_new_item)
            # self.item_model.layoutAboutToBeChanged.emit()
            # self.item_model.layoutChanged.emit()
        elif action == "chg_item":
            logger.debug('Changing item ...')
            if selected_indexes := get_selected_indexes():
                self.item_window = SingleItemWindow(self.item_proxy_model,
                                                    selected_indexes)
                self.item_window.chg_item_signal.connect(self.chg_items)
                # chg_item_signal is emitted from the ok button of SingleItemWindow
                # when changing is done
                # self.item_model.layoutAboutToBeChanged.emit()
                # self.item_model.layoutChanged.emit()
        elif action == "del_item":
            logger.debug('Deleting item ...')
            if selected_indexes := get_selected_indexes():
                self.delete_item(selected_indexes)

    @Slot(pd.DataFrame)
    def add_new_item(self, new_df: pd.DataFrame):
        """
        This is called when SingleItemWindow emits a signal
        :param new_df:
        :return:
        """
        result_msg = self.item_model.add_new_row(new_df)
        logger.debug(f'add_new_item: new item {result_msg} created')
        self.statusBar().showMessage(result_msg)
        self.item_model.layoutAboutToBeChanged.emit()
        self.item_model.layoutChanged.emit()

    @Slot(object)
    def chg_items(self, indexes: List[QModelIndex]):
        """
        This is called when SingleItemWindow emits a signal
        :param indexes:
        :return:
        """
        flag_col = self.item_model.model_df.columns.get_loc('flag')
        for idx in indexes:
            if idx.column() == flag_col:
                self.item_model.set_chg_flag(idx)
                logger.debug(f'chg_items: item {idx.row()} changed')

    def delete_item(self, indexes: List[QModelIndex]):
        '''
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        '''
        flag_col = self.item_model.model_df.columns.get_loc('flag')
        for idx in indexes:
            src_idx = self.item_proxy_model.mapToSource(idx)
            if idx.column() == flag_col:
                self.item_model.set_del_flag(src_idx)
                logger.debug(f'delete_item: items{src_idx.row()} deleted')

    @Slot(str, pd.DataFrame)
    def async_start(self, action: str, df: pd.DataFrame = None):
        """
        Puts async coroutine on the loop through signaling to async_helper
        AsyncHelper will eventually call self.save_to_db(action, df)
        :param action:
        :param df:
        :return:
        """
        self.start_signal.emit(action, df)

    async def save_to_db(self, action: str, df: pd.DataFrame = None):
        """
        This is the function registered to async_helper as a async coroutine
        :param action:
        :param df:
        :return:
        """
        logger.debug(f'{action}')
        if action == "item_save":
            logger.debug('Saving items ...')
            result_str = await self.item_widget.save_to_db()
        self.done_signal.emit()

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = InventoryWindow()
    # async_helper = AsyncHelper(main_window, main_window.save_to_db)

    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()
