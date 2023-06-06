from PySide6.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QComboBox
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel
from di_lab import Lab


class ItemViewDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lab = Lab()
        self.combo_box_items = self.lab.get_etc_datas('category')

    def createEditor(self,
                     parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        editor = QComboBox(parent)
        editor.addItems(self.combo_box_items)
        return editor

    def setEditorData(self,
                      editor: QComboBox,
                      index: QModelIndex) -> None:
        current_value = index.data(Qt.EditRole)
        idx = self.combo_box_items.index(current_value)
        if idx:
            editor.setCurrentIndex(idx)

    def setModelData(self,
                     editor: QComboBox,
                     model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self,
                             editor: QComboBox,
                             option: QStyleOptionViewItem,
                             index: QModelIndex) -> None:
        editor.setGeometry(option.rect)

