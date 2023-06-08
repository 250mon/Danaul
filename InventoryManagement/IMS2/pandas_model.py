import sys
import pandas as pd
from PySide6.QtWidgets import QTableView, QApplication
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List


class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """

    def __init__(self, dataframe: pd.DataFrame = None, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._dataframe = dataframe
        self.editable_cols = []

    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe)

        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole) -> str or None:
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])
        elif role == Qt.EditRole:
            return str(self._dataframe.iloc[index.row(), index.column()])

        return None

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: Qt.ItemDataRole) -> str or None:
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == Qt.Vertical:
                return str(self._dataframe.index[section])

        return None

    def setData(self,
                index: QModelIndex,
                value: str,
                role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            self._dataframe.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index: QModelIndex):
        if index.column() in self.editable_cols:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        # return Qt.NoItemFlags

    def set_editable_cols(self, cols: List):
        self.editable_cols = cols


if __name__ == "__main__":
    app = QApplication(sys.argv)

    df = pd.read_csv("iris.csv")

    view = QTableView()
    view.resize(800, 500)
    view.horizontalHeader().setStretchLastSection(True)
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    model = PandasModel(df)
    view.setModel(model)
    view.show()
    app.exec()
