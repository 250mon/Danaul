import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QHBoxLayout,
    QVBoxLayout, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QFile
from PySide6.QtGui import QAction, QIcon
from ui.login_widget import LoginWidget
from common.async_helper import AsyncHelper
from db.ds_lab import Lab
from common.d_logger import Logs
from constants import UserPrivilege, ConfigReader
from model.patient_model import PatientModel
from ui.patient_widget import PatientWidget


logger = Logs().get_logger("main")


class InventoryWindow(QMainWindow):
    start_signal = Signal(str)
    done_signal = Signal(str)
    edit_lock_signal = Signal(str)
    edit_unlock_signal = Signal(str)
    update_all_signal = Signal()
    import_trs_signal = Signal(pd.DataFrame)

    def __init__(self):
        super().__init__()
        is_test: str = ConfigReader().get_options("Testmode")

        self.login_widget = LoginWidget(self)
        self.login_widget.start_main.connect(self.initUI)
        self.update_all_signal.connect(self.update_all)
        # self.import_trs_signal.connect(self.import_sessions)

        if is_test.lower() == "true":
            self.initUI("test")
        elif is_test.lower() == "admin":
            self.initUI("admin")
        else:
            self.login()

        self.import_widget = None

    def login(self):
        self.login_widget.show()

    @Slot(str)
    def initUI(self, user_name: str):
        self.setWindowTitle("다나을 물리치료")
        self.setup_menu()
        self.async_helper = AsyncHelper(self, self.do_db_work)

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

        change_user_action = QAction(QIcon('../assets/user.png'), 'Change user', self)
        change_user_action.triggered.connect(self.change_user)

        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)
        file_menu.addAction(change_user_action)

        # View menu
        self.inactive_item_action = QAction('Show inactive items', self)
        self.inactive_item_action.setStatusTip('Show inactive items')
        self.inactive_item_action.triggered.connect(self.view_inactive_items)

        view_menu = menubar.addMenu('&View')
        view_menu.addAction(self.inactive_item_action)

        # Admin menu
        reset_pw_action = QAction('Reset password', self)
        reset_pw_action.triggered.connect(self.reset_password)

        self.admin_menu = menubar.addMenu('Admin')
        self.admin_menu.addAction(reset_pw_action)
        self.admin_menu.menuAction().setVisible(False)

    def setup_models(self, user_name):
        self.user_name = user_name
        self.patient_model = PatientModel(self.user_name)

        if self.patient_model.get_user_privilege() == UserPrivilege.Admin:
            self.admin_menu.menuAction().setVisible(True)
        else:
            self.admin_menu.menuAction().setVisible(False)


    def setup_widgets(self):
        self.patient_widget = PatientWidget(self)
        self.patient_widget.set_source_model(self.patient_model)

        self.setMinimumSize(1200, 800)
        self.setMaximumSize(1600, 1000)
        self.patient_widget.setMinimumWidth(400)
        self.patient_widget.setMaximumWidth(500)

        # self.setup_dock_widgets()
        self.setup_central_widget()

    def setup_central_widget(self):
        central_widget = QWidget(self)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.patient_widget)
        hbox2 = QHBoxLayout()
        # hbox2.addWidget(self.tr_widget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)

    def setup_dock_widgets(self):
        patient_dock_widget = QDockWidget('환자', self)
        patient_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        patient_dock_widget.setWidget(self.patient_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, patient_dock_widget)

        # sku_dock_widget = QDockWidget('세부품목', self)
        # sku_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
        #                                 Qt.RightDockWidgetArea)
        # sku_dock_widget.setWidget(self.sku_widget)
        # self.addDockWidget(Qt.TopDockWidgetArea, sku_dock_widget)

        # tr_dock_widget = QDockWidget('거래내역', self)
        # tr_dock_widget.setAllowedAreas(Qt.BottomDockWidgetArea |
        #                                Qt.LeftDockWidgetArea)
        # tr_dock_widget.setWidget(self.tr_widget)
        # self.addDockWidget(Qt.BottomDockWidgetArea, tr_dock_widget)

    @Slot(str)
    def async_start(self, action: str):
        # send signal to AsyncHelper to schedule the guest (asyncio) event loop
        # inside the host(Qt) event loop
        # AsyncHelper will eventually call self.save_to_db(action, action)
        self.start_signal.emit(action)

    async def do_db_work(self, action: str):
        """
        This is the function registered to async_helper as a async coroutine
        :param action:
        :param df:
        :return:
        """
        logger.debug(f"{action}")
        result_str = None
        if action == "patient_save":
            logger.debug("Saving patients...")
            result_str = await self.patient_widget.save_to_db()
            logger.debug("Updating patients ...")
            await self.patient_model.update()
            # await self.sku_model.update()
            # self.tr_model.selected_upper_id = None
            # await self.tr_model.update()
        # elif action == "sku_save":
        #     logger.debug("Saving skus ...")
        #     result_str = await self.sku_widget.save_to_db()
        #     await self.sku_model.update()
        #     self.tr_model.selected_upper_id = None
        #     await self.tr_model.update()
        # elif action == "tr_save":
        #     logger.debug("Saving sessions ...")
        #     await self.sku_widget.save_to_db()
        #     result_str = await self.tr_widget.save_to_db()
        #     await self.sku_model.update()
        #     await self.tr_model.update()
        # elif action == "treatments.update":
        #     await self.treatments.model.update()
        # elif action == "sku_update":
        #     await self.sku_model.update()
        # elif action == "tr_update":
        #     await self.tr_model.update()
        elif action == "all_update":
            await self.patient_model.update()
            # await self.sku_model.update()
            # self.tr_model.selected_upper_id = None
            # await self.tr_model.update()

        self.done_signal.emit(action)

        if result_str is not None:
            QMessageBox.information(self,
                                    '저장결과',
                                    result_str,
                                    QMessageBox.Close)

    def patient_selected(self, patient_id: int):
        """
        A double-click event in the patient view triggers this method,
        and this method consequently calls the sku view to display
        the treatments.selected
        """
        pass
        # self.sku_widget.filter_selection(patient_id)

    def sku_selected(self, treatment_id: int):
        """
        A double-click event in the sku view triggers this method,
        and this method consequently calls transaction view to display
        the sku selected
        """
        pass
        # self.tr_widget.filter_selection(treatment_id)

    def view_inactive_items(self):
        if Lab().show_inactive_items:
            Lab().show_inactive_items = False
            self.inactive_item_action.setText('Show inactive treatments')
        else:
            Lab().show_inactive_items = True
            self.inactive_item_action.setText('Hide inactive treatments')

        self.update_all()

    @Slot()
    def update_all(self):
        self.async_start("all_update")

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

main()
# try:
#     main()
# except Exception as e:
#     logger.error("Unexpected exception! %s", e)
