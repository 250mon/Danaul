import sys, os
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QHBoxLayout,
    QVBoxLayout, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QFile
from PySide6.QtGui import QAction, QIcon
from login_widget import LoginWidget
from async_helper import AsyncHelper
from di_lab import Lab
from di_db import InventoryDb
from item_model import ItemModel
from sku_model import SkuModel
from tr_model import TrModel
from item_widget import ItemWidget
from sku_widget import SkuWidget
from tr_widget import TrWidget
from di_logger import Logs, logging
from constants import CONFIG_FILE, UserPrivilege, ConfigReader
from emr_tr_reader import EmrTransactionReader


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

Lab(InventoryDb(CONFIG_FILE))


class InventoryWindow(QMainWindow):
    start_signal = Signal(str)
    done_signal = Signal(str)
    edit_lock_signal = Signal(str)
    edit_unlock_signal = Signal(str)

    def __init__(self):
        super().__init__()
        is_test: str = ConfigReader(CONFIG_FILE).get_options("Testmode")
        if is_test.lower() == "true":
            self.initUI("test")
        elif is_test.lower() == "admin":
            self.initUI("admin")
        else:
            self.login()

    def login(self):
        self.login_widget = LoginWidget(CONFIG_FILE, self)
        self.login_widget.start_main.connect(self.initUI)
        self.login_widget.show()

    @Slot(str)
    def initUI(self, user_name: str):
        self.setWindowTitle("다나을 재고관리")
        self.setup_menu()
        self.async_helper = AsyncHelper(self, self.save_to_db)

        self.setup_main_window(user_name)

    def setup_main_window(self, user_name):
        self.setup_models(user_name)
        self.setup_widgets()
        self.show()

    def setup_menu(self):
        self.statusBar()
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # File menu
        exit_action = QAction(QIcon('../assets/exit.png'), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QApplication.instance().quit)

        import_tr_action = QAction(QIcon('../assets/import.png'), 'Import transactions', self)
        import_tr_action.setShortcut('Ctrl+O')
        import_tr_action.setStatusTip('Import transactions')
        import_tr_action.triggered.connect(self.show_file_dialog)

        change_user_action = QAction(QIcon('../assets/user.png'), 'Change user', self)
        change_user_action.triggered.connect(self.change_user)

        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)
        file_menu.addAction(import_tr_action)
        file_menu.addAction(change_user_action)

        # Admin menu
        reset_pw_action = QAction('Reset password', self)
        reset_pw_action.triggered.connect(self.reset_password)

        self.admin_menu = menubar.addMenu('Admin')
        self.admin_menu.addAction(reset_pw_action)
        self.admin_menu.menuAction().setVisible(False)

    def setup_models(self, user_name):
        self.user_name = user_name
        self.item_model = ItemModel(self.user_name)
        self.sku_model = SkuModel(self.user_name, self.item_model)
        self.tr_model = TrModel(self.user_name, self.sku_model)

        if self.item_model.get_user_privilege() == UserPrivilege.Admin:
            self.admin_menu.menuAction().setVisible(True)
        else:
            self.admin_menu.menuAction().setVisible(False)


    def setup_widgets(self):
        self.item_widget = ItemWidget(self)
        self.item_widget.set_source_model(self.item_model)

        self.sku_widget = SkuWidget(self)
        self.sku_widget.set_source_model(self.sku_model)

        self.tr_widget = TrWidget(self)
        self.tr_widget.set_source_model(self.tr_model)

        self.setMinimumSize(1200, 1000)
        self.setMaximumSize(1600, 1000)
        self.item_widget.setMinimumWidth(400)
        self.item_widget.setMaximumWidth(500)
        self.sku_widget.setMinimumWidth(800)
        self.sku_widget.setMaximumWidth(1100)
        self.tr_widget.setMinimumWidth(1200)
        self.tr_widget.setMaximumWidth(1600)

        # self.setup_dock_widgets()
        self.setup_central_widget()

    def setup_central_widget(self):
        central_widget = QWidget(self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.item_widget)
        hbox1.addWidget(self.sku_widget)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.tr_widget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def setup_dock_widgets(self):
        item_dock_widget = QDockWidget('품목', self)
        item_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        item_dock_widget.setWidget(self.item_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, item_dock_widget)
        sku_dock_widget = QDockWidget('세부품목', self)
        sku_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                        Qt.RightDockWidgetArea)
        sku_dock_widget.setWidget(self.sku_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, sku_dock_widget)
        tr_dock_widget = QDockWidget('거래내역', self)
        tr_dock_widget.setAllowedAreas(Qt.BottomDockWidgetArea |
                                       Qt.LeftDockWidgetArea)
        tr_dock_widget.setWidget(self.tr_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, tr_dock_widget)

    @Slot(str)
    def async_start(self, action: str):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.save_to_db(action, action)
        self.start_signal.emit(action)

    async def save_to_db(self, action: str):
        """
        This is the function registered to async_helper as a async coroutine
        :param action:
        :param df:
        :return:
        """
        logger.debug(f"{action}")
        if action == "item_save":
            logger.debug("Saving items ...")
            result_str = await self.item_widget.save_to_db()
            logger.debug("Updating items ...")
            await self.item_model.update()
        elif action == "sku_save":
            logger.debug("Saving skus ...")
            result_str = await self.sku_widget.save_to_db()
            await self.sku_model.update()
        elif action == "tr_save":
            logger.debug("Saving transactions ...")
            result_str = await self.sku_widget.save_to_db()
            result_str = await self.tr_widget.save_to_db()
            await self.sku_model.update()
            await self.tr_model.update()
        elif action == "tr_update":
            await self.tr_model.update()
        self.done_signal.emit(action)

    def item_selected(self, item_id: int):
        """
        A double-click event in the item view triggers this method,
        and this method consequently calls the sku view to display
        the item selected
        """
        self.sku_widget.filter_selection(item_id)

    def sku_selected(self, sku_id: int):
        """
        A double-click event in the sku view triggers this method,
        and this method consequently calls transaction view to display
        the sku selected
        """
        self.tr_widget.filter_selection(sku_id)

    def show_file_dialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '../')
        if fname[0]:
            self.import_transactions(fname[0])

    def import_transactions(self, file_name):
        reader = EmrTransactionReader(file_name)
        if reader is None:
            logger.debug("Invalid file")
            return

        codes = self.sku_model.get_bit_codes()
        bit_df = reader.read_df_from(codes)
        if bit_df is None:
            logger.debug("bit_df is None")
        else:
            logger.debug(f"\n{bit_df}")
            # self.tr_widget.filter_no_selection()
            self.tr_model.append_new_rows_from_emr(bit_df)

    def reset_password(self):
        u_name, ok = QInputDialog.getText(self, "Reset Password", "Enter user name:")
        if ok:
            hashed_pw = self.login_widget.encrypt_password("a")
            self.login_widget.insert_user_info(u_name, hashed_pw)

    def change_user(self):
        self.close()
        self.login_widget.start_main.disconnect()
        self.login_widget.start_main.connect(self.setup_main_window)
        self.login_widget.show()


def main():
    app = QApplication(sys.argv)

    # style_file = QFile("qss/aqua.qss")
    # style_file = QFile("qss/dark_orange.qss")
    # style_file = QFile("qss/light_blue.qss")
    style_file = QFile("qss/di_custom.qss")
    style_file.open(QFile.ReadOnly)
    app.setStyleSheet(style_file.readAll().toStdString())

    InventoryWindow()
    app.exec()


try:
    main()
except Exception as e:
    logger.Exception("Unexpected exception! %s", e)
