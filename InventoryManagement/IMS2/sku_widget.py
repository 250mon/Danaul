import os
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QMessageBox
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QFont
from di_logger import Logs, logging
from di_table_widget import InventoryTableWidget
from sku_model import SkuModel


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class SkuWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent

    def set_source_model(self, model: SkuModel):
        """
        Common
        :param model:
        :return:
        """
        self.source_model = model
        self._apply_model()

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # Filtering is performed on item_name column
        search_col_num = self.source_model.get_col_number('item_id')
        self.proxy_model.setFilterKeyColumn(search_col_num)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('sku_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_initial_table_view(self):
        super()._setup_initial_table_view()
        self.table_view.doubleClicked.connect(self.row_double_clicked)
        self.table_view.activated.connect(self.row_activated)

    def _setup_delegate_for_columns(self):
        """
        :return:
        """
        super()._setup_delegate_for_columns()

    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        self.set_col_hidden('item_id')

        title_label = QLabel('세부품목')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.stretch(1)

        # search_bar = QLineEdit(self)
        # search_bar.setPlaceholderText('품목명 입력')
        # search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        search_all_btn = QPushButton('전체조회')
        search_all_btn.clicked.connect(self.filter_no_selection)
        add_sku_btn = QPushButton('추가')
        add_sku_btn.clicked.connect(lambda: self.do_actions("add_sku"))
        chg_sku_btn = QPushButton('수정')
        chg_sku_btn.clicked.connect(lambda: self.do_actions("chg_sku"))
        del_sku_btn = QPushButton('삭제/해제')
        del_sku_btn.clicked.connect(lambda: self.do_actions("del_sku"))
        save_sku_btn = QPushButton('저장')
        if hasattr(self.parent, "async_start"):
            save_sku_btn.clicked.connect(lambda: self.parent.async_start("sku_save"))

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_all_btn)
        hbox2.addStretch(1)
        hbox2.addWidget(add_sku_btn)
        hbox2.addWidget(chg_sku_btn)
        hbox2.addWidget(del_sku_btn)
        hbox2.addWidget(save_sku_btn)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.table_view)
        self.setLayout(vbox)

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        logger.debug(f'do_action: {action}')
        if action == "add_sku":
            logger.debug('Adding sku ...')
            if not self.add_new_row():
                QMessageBox.information(self,
                                        "Failed New Sku",
                                        "품목을 먼저 선택하세요.",
                                        QMessageBox.Close)

        elif action == "chg_sku":
            logger.debug('Changing sku ...')
            if selected_indexes := self._get_selected_indexes():
                self.change_rows_by_delegate(selected_indexes)

        elif action == "del_sku":
            logger.debug('Deleting sku ...')
            if selected_indexes := self._get_selected_indexes():
                self.delete_rows(selected_indexes)


    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A sku being double clicked in the sku view automatically makes
        the transaction view to do filtering to show the transactions of
        the selected sku.
        :param index:
        :return:
        """
        if (flag := self.source_model.get_flag(index)) != '':
            logger.debug(f'row_doble_clicked: row cannot be selected because flag is set({flag})')
            QMessageBox.information(self,
                                    "품목 선택 오류",
                                    "선택된 품목은 새로 추가 되었거나 편집 중으로 저장 한 후 선택해 주세요",
                                    QMessageBox.Close)

        if index.isValid():
            src_idx = self.proxy_model.mapToSource(index)
            if hasattr(self.parent, 'sku_selected'):
                self.parent.sku_selected(src_idx)

    @Slot(QModelIndex)
    def row_activated(self, index: QModelIndex):
        """
        While changing rows, activating other rows would make the change
        to stop.
        :param index:
        :return:
        """
        src_idx = self.proxy_model.mapToSource(index)
        if src_idx.row() not in self.source_model.editable_rows_set:
            self.source_model.clear_editable_rows()
