from PySide6.QtWidgets import (
    QWidget, QStyleOptionViewItem, QDateEdit
)
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel, QDate
from common.datetime_utils import qdate_to_pydate, pydate_to_qdate, date
from ui.default_delegate import DefaultDelegate


class DateEditDelegate(DefaultDelegate):
    def __init__(self, default_date: date, parent=None):
        super().__init__(parent)
        self.default_date = default_date

    def createEditor(self,
                     parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        editor = QDateEdit(parent)
        return editor

    def setEditorData(self,
                      editor: QDateEdit,
                      index: QModelIndex) -> None:
        editor.setDate(pydate_to_qdate(self.default_date))

    def setModelData(self,
                     editor: QDateEdit,
                     model: QAbstractItemModel,
                     index: QModelIndex) -> None:
        py_date = qdate_to_pydate(editor.date())
        model.setData(index, py_date, Qt.EditRole)

    def updateEditorGeometry(self,
                             editor: QDateEdit,
                             option: QStyleOptionViewItem,
                             index: QModelIndex) -> None:
        editor.setGeometry(option.rect)
