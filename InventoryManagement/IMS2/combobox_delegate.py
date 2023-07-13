from PySide6.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QComboBox
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel
from typing import List


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, combobox_items: List, parent=None):
        super().__init__(parent)
        self.combobox_items = combobox_items

    def createEditor(self,
                     parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        editor = QComboBox(parent)
        editor.addItems(self.combobox_items)
        print('editor created')
        return editor

    def setEditorData(self,
                      editor: QComboBox,
                      index: QModelIndex) -> None:
        current_value = index.data(Qt.EditRole)
        # idx is the index of the item in the list
        idx = self.combobox_items.index(current_value)
        if idx:
            # set the current index of combobox to the idx
            editor.setCurrentIndex(idx)
        print('setEditorData')

    def setModelData(self,
                     editor: QComboBox,
                     model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        # get the text which is chosen from the combobox
        value = editor.currentText()
        # set the text value to the model
        model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self,
                             editor: QComboBox,
                             option: QStyleOptionViewItem,
                             index: QModelIndex) -> None:
        editor.setGeometry(option.rect)
