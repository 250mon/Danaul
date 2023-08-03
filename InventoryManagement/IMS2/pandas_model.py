import os
import sys
import pandas as pd
from typing import Dict
from PySide6.QtWidgets import QTableView, QApplication
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List
from constants import EditLevel
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """

    SortRole = Qt.UserRole + 1

    def __init__(self, dataframe: pd.DataFrame = None, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.model_df = dataframe
        self.edit_level = EditLevel.Modifiable
        self.col_idx_edit_lvl = None
        self.all_editable_rows_set = set()
        self.editable_cols_set = set()
        self.editable_rows_set = set()
        self.uneditable_rows_set = set()

    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self.model_df)

        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self.model_df.columns)
        return 0

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> object:
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return str(self.model_df.iloc[index.row(), index.column()])
        elif role == Qt.EditRole:
            return str(self.model_df.iloc[index.row(), index.column()])

        return None

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role=Qt.ItemDataRole) -> str or None:
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.model_df.columns[section])

            if orientation == Qt.Vertical:
                return str(self.model_df.index[section])

        return None

    def setData(self,
                index: QModelIndex,
                value: object,
                role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            self.model_df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    def flags(self, index: QModelIndex):
        if index.row() in self.uneditable_rows_set:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif (index.row() in self.editable_rows_set and
                self.col_idx_edit_lvl[index.column()] <= self.edit_level):
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        # return Qt.NoItemFlags

    def set_edit_level(self, level: EditLevel):
        self.edit_level = level

    def set_column_edit_level(self, col_idx_level: Dict[int, int]):
        self.col_idx_edit_lvl = col_idx_level

    def set_editable_row(self, row: int):
        self.editable_rows_set.add(row)

    def unset_editable_row(self, row: int):
        if row in self.editable_rows_set:
            self.editable_rows_set.remove(row)

    def clear_editable_rows(self):
        self.editable_rows_set.clear()

    def set_editable_columns(self, cols: List):
        self.editable_cols_set.update(cols)

    def set_all_editable_row(self, row: int):
        """
        Makes every column editable for new rows
        :param row:
        :return:
        """
        self.all_editable_rows_set.add(row)
        logger.debug(f'set_all_editable_row: row {row}')

    def unset_all_editable_row(self, row: int):
        if row == -1:
            logger.debug(f'unset_all_editable_row: '
                         f'remove all rows from {self.all_editable_rows_set}')
            self.all_editable_rows_set.clear()
        else:
            logger.debug(f'unset_all_editable_row: '
                         f'remove row {row} from {self.all_editable_rows_set}')
            if row in self.all_editable_rows_set:
                self.all_editable_rows_set.remove(row)
            else:
                logger.warn(f'unset_all_editable_row: cannot find row {row} in the set')

    def set_uneditable_row(self, row: int):
        """
        Makes every column uneditable for deleted rows
        :param row:
        :return:
        """
        self.uneditable_rows_set.add(row)
        logger.debug(f'set_uneditable_row: row {row}')

    def unset_uneditable_row(self, row: int):
        if row == -1:
            logger.debug(f'unset_uneditable_row: '
                         f'remove all rows from {self.uneditable_rows_set}')
            self.uneditable_rows_set.clear()
        else:
            logger.debug(f'unset_uneditable_row: '
                         f'remove row {row} from {self.uneditable_rows_set}')
            if row in self.uneditable_rows_set:
                self.uneditable_rows_set.remove(row)
            else:
                logger.warn(f'unset_uneditable_row: cannot find row {row} int he set')


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
