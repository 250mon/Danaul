import sys, os
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget
from PySide6.QtCore import Qt, Signal, Slot
from login_widget import LoginWidget
from async_helper import AsyncHelper
from di_lab import Lab
from di_db import InventoryDb
from di_logger import Logs, logging
from single_item_window import SingleItemWindow
from item_widget import ItemWidget
from sku_widget import SkuWidget


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

DB_SETTINGS_FILE = 'db_settings'
Lab(InventoryDb(DB_SETTINGS_FILE))


class InventoryWindow(QMainWindow):
    start_signal = Signal(str)
    done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        # self.login()
        self.user_name = None
        self.initializeUI('admin')

    def login(self):
        self.login_widget = LoginWidget(DB_SETTINGS_FILE, self)
        self.login_widget.start_main.connect(self.initializeUI)
        self.login_widget.show()

    @Slot(str)
    def initializeUI(self, user_name: str):
        self.user_name = user_name
        self.setMinimumSize(1500, 800)
        self.setWindowTitle("다나을 재고관리")
        # self.item_model = ItemModel(self.user_name)

        self.setUpMainWindow()

        #
        self. async_helper = AsyncHelper(self, self.save_to_db)

        self.show()

    def setUpMainWindow(self):
        self.item_widget = ItemWidget(self.user_name, self)
        self.item_widget.setMaximumWidth(500)

        item_dock_widget = QDockWidget('품목', self)
        item_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        item_dock_widget.setWidget(self.item_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, item_dock_widget)

        self.sku_widget = SkuWidget(self.user_name, 1)
        self.sku_widget.setMaximumWidth(1000)

        sku_dock_widget = QDockWidget('품목', self)
        sku_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                        Qt.RightDockWidgetArea)
        sku_dock_widget.setWidget(self.sku_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, sku_dock_widget)

    @Slot(str)
    def async_start(self, action: str):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.update_df(action, df)
        self.start_signal.emit(action)

    async def save_to_db(self, action: str):
        """
        This is the function registered to async_helper as a async coroutine
        :param action:
        :param df:
        :return:
        """
        logger.debug(f'{action}')
        if action == "item_save":
            logger.debug('Saving items ...')
            result_str = await self.item_widget.save_to_db()
        self.done_signal.emit(action)

    def item_selected(self, item_id: int):
        print(f"selected {item_id}")
        self.sku_widget.item_selected(item_id)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = InventoryWindow()
    # async_helper = AsyncHelper(main_window, main_window.save_to_db)

    # signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()
