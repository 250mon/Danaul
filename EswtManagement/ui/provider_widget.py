from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QHBoxLayout, QVBoxLayout,
    QLabel, QWidget, QTreeView
)
from PySide6.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QFont
from common.d_logger import Logs
from model.provider_model import ProviderModel
from ui.item_view_helpers import ItemViewHelpers



logger = Logs().get_logger("main")


class ProviderWidget(QWidget):
    def __init__(self, model: ProviderModel, parent: QMainWindow = None):
        super().__init__(parent)
        self.parent: QMainWindow = parent
        self.source_model = model
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
        initial_sort_col_num = self.source_model.get_col_number('provider_id')
        self.proxy_model.sort(initial_sort_col_num, Qt.AscendingOrder)

    def init_ui(self):
        self.provider_view = QTreeView()
        self.item_view_helpers = ItemViewHelpers(self.source_model,
                                                 self.proxy_model,
                                                 self.provider_view,
                                                 self)
        self.provider_view.setModel(self.proxy_model)

        self.provider_view.setRootIsDecorated(False)
        self.provider_view.setAlternatingRowColors(True)
        self.provider_view.setSortingEnabled(True)
        self.provider_view.doubleClicked.connect(self.row_double_clicked)

        title_label = QLabel('치 료 사')
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

        hbox2 = QHBoxLayout()
        hbox2.addWidget(search_bar)

        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.provider_view)
        self.setLayout(vbox)

    @Slot(QModelIndex)
    def row_double_clicked(self, index: QModelIndex):
        """
        A provider being double-clicked in the provider view automatically makes
        the session view to update with the data of the provider.
        :param index:
        :return:
        """
        if index.isValid() and hasattr(self.parent, 'upper_layer_model_selected'):
            provider_id = index.siblingAtColumn(self.source_model.get_col_number('provider_id')).data()
            self.source_model.set_selected_id(provider_id)
            self.parent.upper_layer_model_selected(self.source_model)

    def update_all_views(self):
        """
        Update the views with the latest data from db
        :return:
        """
        self.source_model.set_selected_id(None)
        self.parent.update_all_signal.emit()
