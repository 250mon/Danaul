from PySide6.QtWidgets import (
    QWidget, QStyledItemDelegate, QStyleOptionViewItem, QComboBox
)
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel
from PySide6.QtGui import QPainter, QBrush
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
        return editor

    def setEditorData(self,
                      editor: QComboBox,
                      index: QModelIndex) -> None:
        data_val = index.data(Qt.EditRole)
        # idx is the index of the item in the list
        idx = self.combobox_items.index(data_val)
        if idx:
            # set the current index of combobox to the idx
            editor.setCurrentIndex(idx)

    def setModelData(self,
                     editor: QComboBox,
                     model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        # get the text which is chosen from the combobox
        value = editor.currentText()
        # set the text value to the model
        model.setData(index, value, Qt.EditRole)

    def paint(self,
              painter: QPainter,
              option: QStyleOptionViewItem,
              index: QModelIndex):
        painter.save()

        # painter.setRenderHint(QPainter.Antialiasing, True)
        # painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(Qt.green, Qt.BrushStyle(Qt.SolidPattern)))
        # painter.setBrush(option.palette.highlight())
        # painter.setBrush(option.palette.windowText())
        painter.fillRect(option.rect, painter.brush())

        painter.restore()

    def updateEditorGeometry(self,
                             editor: QComboBox,
                             option: QStyleOptionViewItem,
                             index: QModelIndex) -> None:
        editor.setGeometry(option.rect)
