import os
import platform
import sys
from configparser import ConfigParser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtGui import QAction, QIcon, QImage, QPixmap, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from common.danaul_logger import Logs, resource_path

logger = Logs().get_logger("main")


class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.config = ConfigParser()
        config_path = resource_path("./config.ini")
        self.config.read(config_path)
        self.dir_path = Path(self.config["danaul"]["WorkingDirPath"])
        self.sign_file_path = Path(self.config["danaul"]["SignFilePath"])

    def initUI(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openFile = QAction(QIcon("assets/open.png"), "Open", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Open New File")
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(openFile)

        # open file button
        open_file_btn = QPushButton("Open File")
        open_file_btn.setMaximumWidth(500)
        open_file_btn.clicked.connect(self.showDialog)

        # phone number edit box
        self.tel_le = QLineEdit(self)
        self.tel_le.setMaximumWidth(500)
        self.tel_le.setPlaceholderText("Phone Number")

        # create a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # add widgets to the content layout
        self.display_label = QLabel(self)

        # set the content widget inside the scroll area
        scroll_area.setWidget(self.display_label)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.stretch(1)
        hbox.addWidget(self.tel_le)
        hbox.stretch(1)
        hbox.addWidget(open_file_btn)
        hbox.stretch(1)
        vbox.addLayout(hbox)
        vbox.stretch(1)
        vbox.addWidget(scroll_area)

        central_widget = QWidget(self)
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("File Dialog")
        self.setGeometry(200, 50, 1200, 1000)
        self.show()

    def sign_pic(self, file_path: Path):
        out_file_name = "OUT_" + file_path.stem + ".pdf"

        try:
            # open an image
            with Image.open(file_path) as base_img:
                # paste a sign image
                composite_img = base_img.copy()
                img_sign = Image.open(self.sign_file_path)
                composite_img.paste(img_sign, (470, 430), img_sign)

                # render the text on the image
                img_draw = ImageDraw.Draw(composite_img)
                tel_num = self.tel_le.text()
                # specify the font style
                # set font path
                system = platform.system()
                if system == "Windows":
                    font_path = "C:\\Windows\\Fonts\\gulim.ttc"
                elif system == "Darwin":  # macos
                    font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
                elif system == "Linux":
                    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
                else:
                    raise OSError("Unsupported operating system.")

                # load font
                try:
                    font = ImageFont.truetype(font_path, size=16)
                except IOError:
                    print(f"Font not found {font_path}")
                    font = ImageFont.load_default()  # fallback to default font

                # draw text
                img_draw.text(
                    (730, 1150),
                    "비대면 진료" + "\n환자 전화번호: " + tel_num,
                    font=font,
                    fill="black",
                )

                # composite_img.show()
                composite_img.save(file_path.with_name(out_file_name))
                return composite_img

        except Exception as e:
            logger.debug(f"Error in opening file: {e}")
            return None

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, "Open file", str(self.dir_path))
        logger.debug(f"Opening {fname[0]}")

        if fname[0]:
            pil_img = self.sign_pic(Path(fname[0]))
            if pil_img is None:
                return

            # Convert Pillow image to QPixmap
            pil_img_rgba = pil_img.convert("RGBA")
            data = pil_img_rgba.tobytes("raw", "RGBA")
            qimg = QImage(
                data, pil_img_rgba.width, pil_img_rgba.height, QImage.Format_RGBA8888
            )
            qt_pixmap = QPixmap.fromImage(qimg)
            # qt_pixmap = qt_pixmap.scaled(800, 1000, Qt.KeepAspectRatio)

            self.display_label.setPixmap(qt_pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())
