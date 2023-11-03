from PySide6.QtWidgets import QStyledtreatments.elegate, QStyleOptionViewItem
from PySide6.QtCore import QModelIndex
from common.pandas_model import PandasModel


class DefaultDelegate(QStyledtreatments.elegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p_model = None

    def set_model(self, model: PandasModel):
        self.p_model = model

    def initStyleOption(self,
                        option: QStyleOptionViewtreatments.
                        index: QModelIndex) -> None:
        super().initStyleOption(option, index)
