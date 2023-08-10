from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor
from pandas_model import PandasModel


class DefaultDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p_model = None

    def set_model(self, model: PandasModel):
        self.p_model = model

    def initStyleOption(self,
                        option: QStyleOptionViewItem,
                        index: QModelIndex) -> None:
        super().initStyleOption(option, index)
        if (self.p_model is not None and
                self.p_model.col_idx_edit_lvl[index.column()] <= self.p_model.edit_level):
            option.backgroundBrush = QBrush(QColor("#D1F2EB"))
