import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QComboBox,
    QTableView, QHeaderView, QAbstractItemView,
    QHBoxLayout, QVBoxLayout,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from pandas_model import PandasModel
from di_db import InventoryDb
from di_lab import Lab


class ItemsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.initializeUI()

    async def initializeUI(self):
        self.setMinimumSize(1000, 600)
        self.setWindowTitle("Danaul Inventory - Items")
        await self.createModel()
        self.setUpMainWindow()
        self.show()

    async def createModel(self):
        inventory_db = InventoryDb('db_settings')
        items_df = await Lab(inventory_db).get_df_from_db('items')
        items_df['category'] = items_df['category_id'].map(lab.categories)
        self.model = PandasModel(items_df)

    def setUpMainWindow(self):
        table_view = QTableView(self)
        table_view.resize(800, 500)
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table_view.setModel(self.model)

        main_layout = QVBoxLayout()
        main_layout.addWidget(table_view)
        self.setLayout(main_layout)

async def main():
    app = QApplication(sys.argv)
    ex = ItemsWindow()
    await ex.initializeUI()
    app.exec()


if __name__ == '__main__':
    asyncio.run(main())
