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


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

DB_SETTINGS_FILE = 'db_settings'
Lab(InventoryDb(DB_SETTINGS_FILE))

class InventoryWindow(QMainWindow):
    start_signal = Signal(str, pd.DataFrame)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.login()
        self.user_name = None
        # self.initializeUI()

    def login(self):
        self.login_widget = LoginWidget(DB_SETTINGS_FILE, self)
        self.login_widget.start_main.connect(self.initializeUI)
        self.login_widget.show()

    @Slot(str)
    def initializeUI(self, user_name: str):
        self.user_name = user_name
        self.setMinimumSize(1400, 800)
        self.setWindowTitle("다나을 재고관리")
        self.item_model = ItemModel(self.user_name)

        self.setUpMainWindow()

        self. async_helper = AsyncHelper(self, self.save_to_db)

        self.show()

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

        # QSortFilterProxyModel enables filtering columns and sorting rows
        self.item_proxy_model = QSortFilterProxyModel()
        self.item_proxy_model.setSourceModel(self.item_model)
        # For later use of new item model, we need another proxymodel
        self.new_item_proxy_model = QSortFilterProxyModel()
        # Filtering is performed on item_name column
        search_col_num = self.item_model.model_df.columns.get_loc('item_name')
        self.item_proxy_model.setFilterKeyColumn(search_col_num)
        # Sorting
        initial_sort_col_num = self.item_model.model_df.columns.get_loc('item_id')
        self.item_proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.item_proxy_model.setSortRole(self.item_model.SortRole)

        # Set the model to the view
        self.item_view.setModel(self.item_proxy_model)

        # Set combo delegates for category and valid columns
        # For other columns, it uses default delegates (LineEdit)
        for col_name in self.item_model.editable_col_iloc.keys():
            col_index, val_list = self.item_model.get_editable_cols_combobox_info(col_name)
            combo_delegate = ComboBoxDelegate(val_list, self)
            self.item_view.setItemDelegateForColumn(col_index, combo_delegate)

        # Create widgets in the view
        item_widget = QWidget(self)
        self.item_search_bar = QLineEdit(self)
        self.item_search_bar.setPlaceholderText('품목명 입력')
        self.item_search_bar.textChanged.connect(
            self.item_proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        add_item_btn.clicked.connect(lambda: self.do_actions("add_item"))
        chg_item_btn = QPushButton('수정')
        chg_item_btn.clicked.connect(lambda: self.do_actions("chg_item"))
        del_item_btn = QPushButton('삭제/해제')
        del_item_btn.clicked.connect(lambda: self.do_actions("del_item"))
        save_item_btn = QPushButton('저장')
        save_item_btn.clicked.connect(lambda: self.async_start("save"))

        item_hbox = QHBoxLayout()
        item_hbox.addWidget(self.item_search_bar)
        item_hbox.addStretch(1)
        item_hbox.addWidget(add_item_btn)
        item_hbox.addWidget(chg_item_btn)
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

    @Slot(str, pd.DataFrame)
    def async_start(self, action: str, df: pd.DataFrame = None):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.update_df(action, df)
        self.start_signal.emit(action, df)

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

    async def save_to_db(self, action: str, df: pd.DataFrame = None):
        logger.debug(f'{action}')
        if action == "save":
            logger.debug('Saving ...')
            result = await self.item_model.update_db()
            result_string = '\n'.join(result.values())

            # update model_df
            logger.debug('Updating model_df ...')
            await self.item_model.update_model_df_from_db()
            self.item_model.layoutAboutToBeChanged.emit()
            self.item_model.layoutChanged.emit()

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
    # async_helper = AsyncHelper(main_window, main_window.save_to_db)

    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()
