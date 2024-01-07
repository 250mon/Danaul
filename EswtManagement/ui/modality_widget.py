from typing import Dict
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QMessageBox, QWidget, QTreeView
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from common.async_helper import AsyncHelper
from common.d_logger import Logs
from model.modality_model import ModalityModel
from ui.item_view_helpers import ItemViewHelpers
from ui.register_new_modality_dialog import NewModalityDialog


logger = Logs().get_logger("main")


class ModalityWidget(QWidget):
    def __init__(self, model: ModalityModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.async_helper: AsyncHelper = self.parent.async_helper
        self.source_model = model
        self.proxy_model = None
        # initialize
        self.set_model()
        self.init_ui()

    def set_model(self):
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        # -1 means searching every column
        self.proxy_model.setFilterKeyColumn(-1)

        # Sorting
        # For sorting, model data needs to be read in certain deterministic order
        # we use SortRole to read in model.data() for sorting purpose
        self.proxy_model.setSortRole(self.source_model.SortRole)
        initial_sort_col_num = self.source_model.get_col_number('modality_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def init_ui(self):
        self.modality_view = QTreeView()
        self.item_view_helpers = ItemViewHelpers(self.source_model,
                                                 self.proxy_model,
                                                 self.modality_view,
                                                 self)
        self.modality_view.setModel(self.proxy_model)

        self.modality_view.setRootIsDecorated(False)
        self.modality_view.setAlternatingRowColors(True)
        self.modality_view.setSortingEnabled(True)
        self.modality_view.doubleClicked.connect(self.row_double_clicked)

        self.new_modality_dlg = NewModalityDialog(self.source_model, self)
        self.new_modality_dlg.new_modality_signal.connect(self.item_view_helpers.save_model_to_db)

        title_label = QLabel('치료 형태')
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
        add_btn = QPushButton('추 가')
        add_btn.clicked.connect(self.add_modality)
        del_btn = QPushButton('삭 제')
        del_btn.clicked.connect(self.del_modality)

        edit_hbox = QHBoxLayout()
        edit_hbox.addWidget(add_btn)
        edit_hbox.addWidget(del_btn)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_bar)
        hbox2.addStretch(1)
        hbox2.addLayout(edit_hbox)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.modality_view)
        self.setLayout(vbox)

    @Slot()
    def add_modality(self):
        logger.debug("Adding a modality ...")
        self.new_modality_dlg.update_with_latest_model()
        self.new_modality_dlg.show()

    @Slot()
    def del_modality(self):
        logger.debug("Deleting modality ...")
        if selected_indexes := self.item_view_helpers.get_selected_indexes():
            logger.debug(f"del_modality {selected_indexes}")
            self.item_view_helpers.delete_rows(selected_indexes)
            self.item_view_helpers.save_model_to_db()

    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A modality being double-clicked in the modality view automatically makes
        the session view to update with the data of the modality.
        :param index:
        :return:
        """
        if index.isValid() and hasattr(self.parent, 'upper_layer_model_selected'):
            modality_id = index.siblingAtColumn(self.source_model.get_col_number('modality_id')).data()
            self.source_model.set_selected_id(modality_id)
            self.parent.upper_layer_model_selected(self.source_model)

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        # if there is remaining unsaved new rows, drop them
        self.source_model.del_new_rows()
        self.source_model.set_selected_id(None)
        self.parent.update_all_signal.emit()