import os
import pandas as pd
from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QPushButton, QLineEdit,
    QTableView, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QSortFilterProxyModel, QModelIndex, QRegularExpression
)
from sku_model import SkuModel
from di_logger import Logs, logging
from combobox_delegate import ComboBoxDelegate

logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class SkuWidget(QWidget):
    def __init__(self, user_name, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.user_name = user_name
        self.sku_model = SkuModel(self.user_name)
        self.setup_sku_view()
        self.setup_ui()

    def setup_sku_view(self):
        # skus view
        self.sku_view = QTableView(self)
        self.sku_view.horizontalHeader().setStretchLastSection(True)
        self.sku_view.setAlternatingRowColors(True)
        self.sku_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.sku_view.resizeColumnsToContents()
        self.sku_view.setSortingEnabled(True)

        # QSortFilterProxyModel enables filtering columns and sorting rows
        self.sku_proxy_model = QSortFilterProxyModel()
        self.sku_proxy_model.setSourceModel(self.sku_model)
        # For later use of new sku model, we need another proxymodel
        self.new_sku_proxy_model = QSortFilterProxyModel()
        # Filtering is performed on item_name column
        search_col_num = self.sku_model.model_df.columns.get_loc('item_id')
        self.sku_proxy_model.setFilterKeyColumn(search_col_num)
        # Sorting
        initial_sort_col_num = self.sku_model.model_df.columns.get_loc('sku_id')
        self.sku_proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.sku_proxy_model.setSortRole(self.sku_model.SortRole)

        # Set the model to the view
        self.sku_view.setModel(self.sku_proxy_model)

        # Set combo delegates for category and valid columns
        # For other columns, it uses default delegates (LineEdit)
        for col_name in self.sku_model.editable_col_iloc.keys():
            col_index, val_list = self.sku_model.get_editable_cols_combobox_info(col_name)
            combo_delegate = ComboBoxDelegate(val_list, self)
            self.sku_view.setItemDelegateForColumn(col_index, combo_delegate)

    def setup_ui(self):
        self.sku_search_bar = QLineEdit(self)
        self.sku_search_bar.setPlaceholderText('품목명 입력')
        self.sku_search_bar.textChanged.connect(
            self.sku_proxy_model.setFilterFixedString)
        add_sku_btn = QPushButton('추가')
        add_sku_btn.clicked.connect(lambda: self.do_actions("add_sku"))
        chg_sku_btn = QPushButton('수정')
        chg_sku_btn.clicked.connect(lambda: self.do_actions("chg_sku"))
        del_sku_btn = QPushButton('삭제/해제')
        del_sku_btn.clicked.connect(lambda: self.do_actions("del_sku"))
        save_sku_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_sku_btn.clicked.connect(lambda: self.parent.async_start("sku_save"))
        sku_hbox = QHBoxLayout()
        sku_hbox.addWidget(self.sku_search_bar)
        sku_hbox.addStretch(1)
        sku_hbox.addWidget(add_sku_btn)
        sku_hbox.addWidget(chg_sku_btn)
        sku_hbox.addWidget(del_sku_btn)
        sku_hbox.addWidget(save_sku_btn)
        sku_vbox = QVBoxLayout()
        sku_vbox.addLayout(sku_hbox)
        sku_vbox.addWidget(self.sku_view)
        self.setLayout(sku_vbox)

    @Slot(str, pd.DataFrame)
    def do_actions(self, action: str, df: pd.DataFrame = None):
        def get_selected_indexes():
            # the indexes of proxy model
            selected_indexes = self.sku_view.selectedIndexes()
            check_indexes = [idx.isValid() for idx in selected_indexes]
            if len(selected_indexes) > 0 and False not in check_indexes:
                logger.debug(f'Indexes selected: {selected_indexes}')
                return selected_indexes
            else:
                logger.debug(f'Indexes not selected or invalid: {selected_indexes}')
                return None

        logger.debug(f'{action}')
        if action == "add_sku":
            logger.debug('Adding sku ...')
            self.add_new_sku_by_delegate()

        elif action == "del_sku":
            logger.debug('Deleting sku ...')
            if selected_indexes := get_selected_indexes():
                self.delete_sku(selected_indexes)

    @Slot(str, pd.DataFrame)
    def async_start(self, action: str, df: pd.DataFrame = None):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.update_df(action, df)
        self.start_signal.emit(action, df)

    @Slot(pd.DataFrame)
    def add_new_sku_by_delegate(self, new_df: pd.DataFrame):
        """
        This is called when SingleSkuWindow emits a signal
        :param new_df:
        :return:
        """
        result_msg = self.sku_model.add_new_row(new_df)
        logger.debug(f'add_new_sku: new sku {result_msg} created')
        self.parent.statusBar().showMessage(result_msg)
        self.sku_model.layoutAboutToBeChanged.emit()
        self.sku_model.layoutChanged.emit()

        row_count = self.sku_model.rowCount()
        new_item_index = self.sku_model.index(row_count - 1, 0)
        self.sku_model.set_new_flag(new_item_index)

    @Slot(object)
    def chg_skus(self, indexes: List[QModelIndex]):
        """
        This is called when SingleSkuWindow emits a signal
        :param indexes:
        :return:
        """
        flag_col = self.sku_model.model_df.columns.get_loc('flag')
        for idx in indexes:
            if idx.column() == flag_col:
                self.sku_model.set_chg_flag(idx)
                logger.debug(f'chg_skus: sku {idx.row()} changed')

    def delete_sku(self, indexes: List[QModelIndex]):
        '''
        This is called from a Button
        Just tagging as 'deleted' in flag column instead of dropping
        Actual dropping is done during saving into DB
        :param indexes:
        :return:
        '''
        flag_col = self.sku_model.model_df.columns.get_loc('flag')
        for idx in indexes:
            src_idx = self.sku_proxy_model.mapToSource(idx)
            if idx.column() == flag_col:
                self.sku_model.set_del_flag(src_idx)
                logger.debug(f'delete_sku: skus{src_idx.row()} deleted')

    async def save_to_db(self):
        result_str = await self.sku_model.update_db()
        if result_str is not None:
            QMessageBox.information(self,
                                    'Save Results',
                                    result_str,
                                    QMessageBox.Close)
        # update model_df
        logger.debug('Updating model_df ...')
        await self.sku_model.update_model_df_from_db()
        self.sku_model.layoutAboutToBeChanged.emit()
        self.sku_model.layoutChanged.emit()

        return result_str

    def filter_selected_item(self, item_id: int):
        self.sku_proxy_model.setFilterFixedString(str(item_id))