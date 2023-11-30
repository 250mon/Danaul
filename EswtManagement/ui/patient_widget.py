from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QFont
from common.d_logger import Logs
from ui.di_table_widget import InventoryTableWidget
from model.provider_model import ProviderModel
from ui.single_provider_window import SingleProviderWindow


logger = Logs().get_logger("main")


class ProviderWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.delegate_mode = True

    def set_source_model(self, model: ProviderModel):
        self.source_model = model
        self._apply_model()

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('provider_name')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def _setup_initial_table_view(self):
        """
        Carried out before the model is set to the table view
        :return:
        """
        super()._setup_initial_table_view()
        self.table_view.doubleClicked.connect(self.row_double_clicked)

    def _setup_ui(self):
        """
        Needs to be implemented
        :return:
        """
        self.set_col_hidden('provider_id')
        self.set_col_width("provider_name", 50)

        title_label = QLabel('환자')
        font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(font)
        refresh_btn = QPushButton('전체새로고침')
        refresh_btn.clicked.connect(self.update_all_views)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(title_label)
        hbox1.stretch(1)
        hbox1.addWidget(refresh_btn)

        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText('검색어')
        search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        add_btn = QPushButton('신환')
        add_btn.clicked.connect(self.add_provider)
        del_btn = QPushButton('삭제')
        del_btn.clicked.connect(self.del_provider)
        save_btn = QPushButton('저장')
        save_btn.clicked.connect(self.save_model_to_db)

        self.edit_mode = QGroupBox("편집 모드")
        self.edit_mode.setCheckable(True)
        self.edit_mode.setChecked(False)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(add_btn)
        edit_hbox.addWidget(del_btn)
        edit_hbox.addWidget(save_btn)
        self.edit_mode.setLayout(edit_hbox)
        self.edit_mode.clicked.connect(self.edit_mode_clicked)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_bar)
        hbox2.addStretch(1)
        hbox2.addWidget(self.edit_mode)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.table_view)
        self.setLayout(vbox)

    @Slot(str)
    def enable_edit_mode(self, sender: str):
        if sender != "treatment_widget":
            self.edit_mode.setEnabled(True)

    @Slot(str)
    def disable_edit_mode(self, sender: str):
        if sender != "treatment_widget":
            self.edit_mode.setEnabled(False)

    @ Slot(bool)
    def edit_mode_clicked(self, checked):
        if checked:
            logger.debug("Now enter into edit mode")
            self.edit_mode_starts()
        elif self.source_model.is_model_editing():
            logger.debug("The model is in the middle of editing."
                         ' Should save before exit the mode')
            QMessageBox.information(self,
                                    '편집모드 중 종료',
                                    '편집모드를 종료하려면 수정부분에 대해 먼저 저장하시거나 삭제해주세요',
                                    QMessageBox.Close)
            self.edit_mode.setChecked(True)
        else:
            logger.debug("Now edit mode ends")
            self.edit_mode_ends()

    def edit_mode_starts(self):
        self.source_model.set_editable(True)
        self.parent.edit_lock_signal.emit("treatment_widget")

    def edit_mode_ends(self):
        self.source_model.set_editable(False)
        self.parent.edit_unlock_signal.emit("treatment_widget")

    @Slot()
    def add_provider(self):
        logger.debug("Adding a provider ...")
        self.add_new_row()
        if not self.delegate_mode:
            # Input window mode using DataMapperWidget
            new_pt_index = self.source_model.index(self.source_model.rowCount() - 1, 0)
            self.provider_window = SingleProviderWindow(self.proxy_model,
                                                      new_pt_index,
                                                      self)

    @Slot()
    def del_provider(self):
        logger.debug("Deleting provider ...")
        if selected_indexes := self._get_selected_indexes():
            logger.debug(f"del_provider {selected_indexes}")
            self.delete_rows(selected_indexes)

    @Slot()
    def chg_provider(self):
            logger.debug("Changing provider ...")
            if selected_indexes := self._get_selected_indexes():
                logger.debug(f"chg_provider {selected_indexes}")
                # if self.delegate_mode:
                #     self.change_rows_by_delegate(selected_indexes)
                if not self.delegate_mode:
                    self.provider_window = SingleProviderWindow(self.proxy_model,
                                                              selected_indexes,
                                                              self)

    def save_model_to_db(self):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        if hasattr(self.parent, "async_start"):
            self.parent.async_start("provider_save")
        self.edit_mode.setChecked(False)
        self.edit_mode_ends()

    @Slot(object)
    def added_new_provider_by_single_item_window(self, index: QModelIndex):
        """
        This is called when SingleItemWindow emits a signal
        It validates the newly added treatments. If it fails, remove it.
        index is indicating the treatment_id column of a new item
        :return:
        """
        if self.source_model.is_flag_column(index):
            logger.debug(f"provider {index.row()} added")

        src_idx = self.proxy_model.mapToSource(index)
        if hasattr(self.source_model, "validate_new_row"):
            if not self.source_model.validate_new_row(src_idx):
                self.source_model.drop_rows([src_idx])

    @Slot(object)
    def changed_providers_by_single_item_window(self, indexes: List[QModelIndex]):
        """
        This is called when SingleItemWindow emits a signal
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                self.source_model.set_chg_flag(idx)
                logger.debug(f"providers {idx.row()} changed")


    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        An treatments.being double clicked in the treatments.view automatically makes
        the sku view to do filtering to show the skus of the selected treatments.
        :param index:
        :return:
        """
        if not self.edit_mode.isChecked() and index.isValid() and hasattr(
                self.parent, 'provider_selected'):
            provider_id = index.siblingAtColumn(self.source_model.get_col_number('provider_id')).data()
            self.parent.provider_selected(provider_id)

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        self.parent.update_all_signal.emit()