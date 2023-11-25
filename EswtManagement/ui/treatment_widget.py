import os
from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QFont
from common.d_logger import Logs, logging
from ui.di_table_widget import InventoryTableWidget
from model.treatment_model import TreatmentModel
from ui.single_item_window import SingleItemWindow


class TreatmentWidget(InventoryTableWidget):
    def __init__(self, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.delegate_mode = True

        self.logger = Logs().get_logger(os.path.basename(__file__))
        self.logger.setLevel(logging.DEBUG)

    def set_source_model(self, model: TreatmentModel):
        self.source_model = model
        self._apply_model()

    def _setup_proxy_model(self):
        """
        Needs to be implemented
        :return:
        """
        # Filtering is performed on treatment_name column
        # search_col_num = self.source_model.get_col_number('treatment_name')
        # self.proxy_model.setFilterKeyColumn(search_col_num)

        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('treatment_id')
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
        self.set_col_hidden('category_id')
        self.set_col_width("treatment_id", 50)
        self.set_col_width("active", 50)
        self.set_col_width("treatment_name", 150)
        self.set_col_width("description", 150)

        title_label = QLabel('품목')
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
        add_btn = QPushButton('추가')
        add_btn.clicked.connect(lambda: self.do_actions("add_treatment"))
        del_btn = QPushButton('삭제/해제')
        del_btn.clicked.connect(lambda: self.do_actions("del_treatment"))
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
            self.logger.debug("Now enter into edit mode")
            self.edit_mode_starts()
        elif self.source_model.is_model_editing():
            self.logger.debug("The model is in the middle of editing."
                         ' Should save before exit the mode')
            QMessageBox.information(self,
                                    '편집모드 중 종료',
                                    '편집모드를 종료하려면 수정부분에 대해 먼저 저장하시거나 삭제해주세요',
                                    QMessageBox.Close)
            self.edit_mode.setChecked(True)
        else:
            self.logger.debug("Now edit mode ends")
            self.edit_mode_ends()

    def edit_mode_starts(self):
        self.source_model.set_editable(True)
        self.parent.edit_lock_signal.emit("treatment_widget")

    def edit_mode_ends(self):
        self.source_model.set_editable(False)
        self.parent.edit_unlock_signal.emit("treatment_widget")

    @Slot(str)
    def do_actions(self, action: str):
        """
        Needs to be implemented
        :param action:
        :return:
        """
        self.logger.debug(f"{action}")
        if action == "add_treatment":
            self.logger.debug("Adding treatment ...")
            self.add_new_row()
            if not self.delegate_mode:
                # Input window mode using DataMapperWidget
                new_treatment_index = self.source_model.index(self.source_model.rowCount()-1, 0)
                self.treatments.window = SingleItemWindow(self.proxy_model,
                                                    new_treatment_index, self)

        elif action == "chg_treatment":
            self.logger.debug("Changing treatment ...")
            if selected_indexes := self._get_selected_indexes():
                self.logger.debug(f"chg_treatment_{selected_indexes}")
                # if self.delegate_mode:
                #     self.change_rows_by_delegate(selected_indexes)
                if not self.delegate_mode:
                    self.treatments.window = SingleItemWindow(self.proxy_model,
                                                        selected_indexes, self)

        elif action == "del_treatment":
            self.logger.debug("Deleting treatment ...")
            if selected_indexes := self._get_selected_indexes():
                self.logger.debug(f"del_treatment_{selected_indexes}")
                self.delete_rows(selected_indexes)

    def save_model_to_db(self):
        """
        Save the model to DB
        It calls the inventory view's async_start() which calls back the model's
        save_to_db()
        :return:
        """
        if hasattr(self.parent, "async_start"):
            self.parent.async_start("treatments.save")
        self.edit_mode.setChecked(False)
        self.edit_mode_ends()

    @Slot(object)
    def added_new_treatment_by_single_item_window(self, index: QModelIndex):
        """
        This is called when SingleItemWindow emits a signal
        It validates the newly added treatments. If it fails, remove it.
        index is indicating the treatment_id column of a new item
        :return:
        """
        if self.source_model.is_flag_column(index):
            self.logger.debug(f"treatments.{index.row()} added")

        src_idx = self.proxy_model.mapToSource(index)
        if hasattr(self.source_model, "validate_new_row"):
            if not self.source_model.validate_new_row(src_idx):
                self.source_model.drop_rows([src_idx])

    @Slot(object)
    def changed_treatments_by_single_item_window(self, indexes: List[QModelIndex]):
        """
        This is called when SingleItemWindow emits a signal
        :param indexes:
        :return:
        """
        for idx in indexes:
            if self.source_model.is_flag_column(idx):
                self.source_model.set_chg_flag(idx)
                self.logger.debug(f"treatments {idx.row()} changed")


    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        An treatments.being double clicked in the treatments.view automatically makes
        the sku view to do filtering to show the skus of the selected treatments.
        :param index:
        :return:
        """
        if not self.edit_mode.isChecked() and index.isValid() and hasattr(
                self.parent, 'treatments.selected'):
            treatment_id = index.siblingAtColumn(self.source_model.get_col_number('treatment_id')).data()
            self.parent.treatments.selected(treatment_id)

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        self.parent.update_all_signal.emit()
