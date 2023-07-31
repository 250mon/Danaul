import os
import pandas as pd
from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMessageBox, QPushButton, QLineEdit,
    QTableView, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QSortFilterProxyModel, QModelIndex
)
from item_model import ItemModel
from temp_item_model import TempItemModel
from di_logger import Logs, logging
from combobox_delegate import ComboBoxDelegate
from single_item_window import SingleItemWindow


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class ItemWidget(QWidget):
    def __init__(self, user_name, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.user_name = user_name
        self.delegate_mode = True
        if self.delegate_mode:
            self.item_model = ItemModel(self.user_name)
        else:
            self.item_model = TempItemModel(self.user_name)
        self.setup_item_view()
        self.setup_ui()

    def setup_item_view(self):
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
        self.item_view.doubleClicked.connect(self.item_double_clicked)
        self.item_view.activated.connect(self.item_activated)

        # QSortFilterProxyModel enables filtering columns and sorting rows
        self.item_proxy_model = QSortFilterProxyModel()
        # For later use of new item model, we need another proxy model
        self.new_item_proxy_model = QSortFilterProxyModel()
        # Set the model to the view
        self.item_view.setModel(self.item_proxy_model)

        # Set the source model
        self.item_proxy_model.setSourceModel(self.item_model)

        # Filtering is performed on item_name column
        search_col_num = self.item_model.model_df.columns.get_loc('item_name')
        self.item_proxy_model.setFilterKeyColumn(search_col_num)

        # Sorting
        initial_sort_col_num = self.item_model.model_df.columns.get_loc('item_id')
        self.item_proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.item_proxy_model.setSortRole(self.item_model.SortRole)


        # Set combo delegates for category and valid columns
        # For other columns, it uses default delegates (LineEdit)
        for col_name in self.item_model.editable_col_iloc.keys():
            if col_name != 'description':
                col_index, val_list = self.item_model.get_editable_cols_combobox_info(col_name)
                combo_delegate = ComboBoxDelegate(val_list, self)
                self.item_view.setItemDelegateForColumn(col_index, combo_delegate)

    def setup_ui(self):
        item_search_bar = QLineEdit(self)
        item_search_bar.setPlaceholderText('품목명 입력')
        item_search_bar.textChanged.connect(
            self.item_proxy_model.setFilterFixedString)
        add_item_btn = QPushButton('추가')
        add_item_btn.clicked.connect(lambda: self.do_actions("add_item"))
        chg_item_btn = QPushButton('수정')
        chg_item_btn.clicked.connect(lambda: self.do_actions("chg_item"))
        del_item_btn = QPushButton('삭제/해제')
        del_item_btn.clicked.connect(lambda: self.do_actions("del_item"))
        save_item_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_item_btn.clicked.connect(lambda: self.parent.async_start("item_save"))
        item_hbox = QHBoxLayout()
        item_hbox.addWidget(item_search_bar)
        item_hbox.addStretch(1)
        item_hbox.addWidget(add_item_btn)
        item_hbox.addWidget(chg_item_btn)
        item_hbox.addWidget(del_item_btn)
        item_hbox.addWidget(save_item_btn)
        item_vbox = QVBoxLayout()
        item_vbox.addLayout(item_hbox)
        item_vbox.addWidget(self.item_view)
        self.setLayout(item_vbox)

    @Slot(str, pd.DataFrame)
    def do_actions(self, action: str):
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
            if self.delegate_mode:
                # Delegate mode
                self.add_new_item_by_delegate()
            else:
                # Input window mode using DataMapperWidget
                new_item_model = TempItemModel(self.user_name, template_flag=True)
                self.new_item_proxy_model.setSourceModel(new_item_model)
                self.item_window = SingleItemWindow(self.new_item_proxy_model, None, self)

        elif action == "chg_item":
            logger.debug('Changing item ...')
            if selected_indexes := get_selected_indexes():
                if self.delegate_mode:
                    self.change_items_by_delegate(selected_indexes)
                else:
                    self.item_window = SingleItemWindow(self.item_proxy_model,
                                                        selected_indexes, self)

        elif action == "del_item":
            logger.debug('Deleting item ...')
            if selected_indexes := get_selected_indexes():
                self.delete_items(selected_indexes)


    @Slot(pd.DataFrame)
    def add_new_item(self, new_df: pd.DataFrame):
        """
        This is called when SingleItemWindow emits a signal
        :param new_df:
        :return:
        """
        result_msg = self.item_model.add_new_row_by_widget(new_df)
        logger.debug(f'add_new_item: new item {result_msg} created')
        self.parent.statusBar().showMessage(result_msg)
        self.item_model.layoutAboutToBeChanged.emit()
        self.item_model.layoutChanged.emit()

    def add_new_item_by_delegate(self):
        """
        This is called from a Button
        :return:
        """
        self.item_model.add_new_row_by_delegate()
        logger.debug(f'add_new_item: new item is being created')
        self.parent.statusBar().showMessage('A new row being created')
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
                logger.debug(f'chg_items: items {idx.row()} changed')

    def change_items_by_delegate(self, indexes: List[QModelIndex]):
        '''
        This is called from a Button
        Just tagging as 'changed' in flag column and allowing the user
        to modify the items
        :param indexes:
        :return:
        '''
        flag_col = self.item_model.model_df.columns.get_loc('flag')
        for idx in indexes:
            src_idx = self.item_proxy_model.mapToSource(idx)
            if idx.column() == flag_col:
                self.item_model.set_chg_flag(src_idx)
                logger.debug(f'change_items_by_delegate: items {src_idx.row()} changed')

    def delete_items(self, indexes: List[QModelIndex]):
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
                logger.debug(f'delete_items: items {src_idx.row()} deleted')

    async def save_to_db(self):
        result_str = await self.item_model.update_db()
        if result_str is not None:
            QMessageBox.information(self,
                                    'Save Results',
                                    result_str,
                                    QMessageBox.Close)
        # update model_df
        logger.debug('Updating model_df ...')
        await self.item_model.update_model_df_from_db()
        self.item_model.layoutAboutToBeChanged.emit()
        self.item_model.layoutChanged.emit()

        return result_str

    @Slot(QModelIndex)
    def item_double_clicked(self, index: QModelIndex):
        """
        An item being double clicked in item view automatically makes
        the sku view to do filtering to show the skus of the item only.
        :param index:
        :return:
        """
        if index.isValid():
            src_idx = self.item_proxy_model.mapToSource(index)
            item_id = int(src_idx.siblingAtColumn(0).data())
            self.parent.item_selected(item_id)

    @Slot(QModelIndex)
    def item_activated(self, index: QModelIndex):
        """
        While changing items, activating other items would make changing
        to stop.
        :param index:
        :return:
        """
        src_idx = self.item_proxy_model.mapToSource(index)
        if src_idx.row() not in self.item_model.editable_rows_set:
            self.item_model.clear_editable_rows()
