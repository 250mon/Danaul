import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QHBoxLayout,
    QInputDialog, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QFile
from PySide6.QtGui import QAction, QIcon
from common.async_helper import AsyncHelper
from common.d_logger import Logs
from db.ds_lab import Lab
from model.di_data_model import DataModel
from ui.login_widget import LoginWidget
from ui.patient_widget import PatientWidget, PatientModel
from ui.provider_widget import ProviderWidget, ProviderModel
from ui.modality_widget import ModalityWidget, ModalityModel
from ui.bodypart_widget import BodyPartWidget, BodyPartModel
from ui.session_widget import SessionWidget, SessionModel
from constants import ConfigReader, ADMIN_GROUP


logger = Logs().get_logger("main")


class TreatmentWindow(QMainWindow):
    update_all_signal = Signal()
    import_trs_signal = Signal(pd.DataFrame)
    async_start_signal = Signal(str)
    async_done_signal = Signal(str)

    def __init__(self):
        super().__init__()
        is_test: str = ConfigReader().get_options("Testmode")

        self.login_widget = LoginWidget(self)
        self.login_widget.start_main.connect(self.start_app)

        self.async_helper: AsyncHelper = None

        if is_test.lower() == "true":
            self.start_app("test")
        elif is_test.lower() == "admin":
            self.start_app("admin")
        else:
            self.login()

        self.async_start_signal.connect(self.async_helper.on_worker_started)
        self.async_done_signal.connect(self.async_helper.on_worker_done)
        self.update_all_signal.connect(self.update_all)

    def login(self):
        self.login_widget.show()

    @Slot(str)
    def start_app(self, user_name: str):
        self.setup_models(user_name)
        self.async_helper = AsyncHelper(self, self.do_db_work)
        self.init_ui(user_name)

    def setup_models(self, user_name):
        self.patient_model = PatientModel(user_name)
        self.provider_model = ProviderModel(user_name)
        self.modality_model = ModalityModel(user_name)
        self.part_model = BodyPartModel(user_name)
        self.session_model = SessionModel(user_name)

    def init_ui(self, user_name):
        self.setWindowTitle("다나을 물리치료")
        self.setup_menu()
        self.setup_child_widgets()
        self.setup_central_widget()
        self.show_ui(user_name)

    def show_ui(self, user_name: str):
        if user_name in ADMIN_GROUP:
            self.admin_menu.menuAction().setVisible(True)
            self.session_widget.set_admin_menu_enabled(True)
        else:
            self.admin_menu.menuAction().setVisible(False)
            self.session_widget.set_admin_menu_enabled(False)
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

    def setup_child_widgets(self):
        self.patient_widget = PatientWidget(self.patient_model, self)
        self.patient_widget.set_async_helper(self.async_helper)
        self.provider_widget = ProviderWidget(self.provider_model, self)
        self.modality_widget = ModalityWidget(self.modality_model, self)
        self.modality_widget.set_async_helper(self.async_helper)
        self.part_widget = BodyPartWidget(self.part_model, self)
        self.part_widget.set_async_helper(self.async_helper)
        self.session_widget = SessionWidget(self.session_model, self)
        self.session_widget.set_async_helper(self.async_helper)

        self.left_pane = QTabWidget(self)
        self.left_pane.addTab(self.patient_widget, '환자')
        self.left_pane.addTab(self.provider_widget, '치료사')
        self.left_pane.addTab(self.modality_widget, '치료 형태')
        self.left_pane.addTab(self.part_widget, '치료 부위')

        self.setMinimumSize(1200, 800)
        self.setMaximumSize(1600, 1000)
        self.left_pane.setMinimumWidth(300)
        self.left_pane.setMaximumWidth(500)
        self.session_widget.setMinimumWidth(900)
        self.session_widget.setMaximumWidth(900)

    def setup_central_widget(self):
        central_widget = QWidget(self)

        # vbox1 = QVBoxLayout()
        # vbox1.addWidget(self.provider_widget)
        # vbox1.addWidget(self.patient_widget)

        hbox = QHBoxLayout()
        # hbox.addLayout(vbox1)
        hbox.addWidget(self.left_pane)
        hbox.addWidget(self.session_widget)
        central_widget.setLayout(hbox)
        self.setCentralWidget(central_widget)

    def setup_dock_widgets(self):
        patient_dock_widget = QDockWidget('환자', self)
        patient_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea |
                                         Qt.LeftDockWidgetArea)
        patient_dock_widget.setWidget(self.patient_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, patient_dock_widget)

    async def do_db_work(self, action: str):
        """
        This is the function registered to async_helper as a async coroutine
        :param action:
        :param df:
        :return:
        """
        logger.debug(f"{action}")
        result_str = None
        if action == "patients_save":
            logger.debug("Saving patients...")
            result_str = await self.patient_model.save_to_db()
            logger.debug("Updating patients ...")
            await self.patient_model.update()
            # self.session_model.set_upper_model(None)
            # await self.session_model.update()
        elif action == "modalities_save":
            logger.debug("Saving modality ...")
            await self.modality_model.save_to_db()
            await self.modality_model.update()
        elif action == "body_parts_save":
            logger.debug("Saving body part ...")
            await self.part_model.save_to_db()
            await self.part_model.update()
        elif action == "sessions_save":
            logger.debug("Saving sessions ...")
            await self.session_model.save_to_db()
            await self.session_model.update()
        elif action == "patients_update":
            await self.patient_model.update()
        elif action == "providers_update":
            await self.provider_model.update()
        elif action == "modalities_update":
            await self.provider_model.update()
        elif action == "sessions_update":
            await self.session_model.update()
        elif action == "all_update":
            await self.patient_model.update()
            await self.provider_model.update()
            await self.modality_model.update()
            await self.session_model.update()

        self.async_done_signal.emit(action)

        if result_str is not None:
            QMessageBox.information(self,
                                    '저장결과',
                                    result_str,
                                    QMessageBox.Close)

    def upper_layer_model_selected(self, upper_model: DataModel):
        """
        A double-click event in the left pane view triggers this method,
        and this method consequently calls the session view to display
        the items for id selected
        """
        self.session_widget.update_with_selected_upper_layer(upper_model)

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
        self.login_widget.start_main.connect(self.show_ui)
        self.login_widget.show()


def main():
    app = QApplication(sys.argv)

    # style_file = QFile("qss/aqua.qss")
    # style_file = QFile("qss/dark_orange.qss")
    # style_file = QFile("qss/light_blue.qss")
    style_file = QFile("qss/di_custom.qss")
    style_file.open(QFile.ReadOnly)
    app.setStyleSheet(style_file.readAll().toStdString())

    TreatmentWindow()
    app.exec()


main()
