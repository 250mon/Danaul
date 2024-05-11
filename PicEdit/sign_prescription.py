from io import open_code
import sys
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QFileDialog, QWidget
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QAction, QPixmap, QImage
from danaul_logger import Logs


logger = Logs().get_logger("main")


class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.dir_path = Path('/Users/danaul/Downloads/')

    def initUI(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openFile = QAction(QIcon('assets/open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open New File')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.display_window = QLabel(self)
        open_file_btn = QPushButton('Open File')
        open_file_btn.clicked.connect(self.showDialog)

        vbox = QVBoxLayout()
        vbox.addWidget(open_file_btn)
        vbox.addWidget(self.display_window)

        central_widget = QWidget(self)
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        self.setWindowTitle('File Dialog')
        self.setGeometry(300, 300, 800, 1200)
        self.show()

    def sign_pic(self, file_path: Path):
        out_file_name = 'OUT_' + file_path.stem + '.pdf'

        try:
            # Open an Image
            with Image.open(file_path) as base_img:
                img_sign = Image.open('jye_sign.png')

                composite_img = base_img.copy()
                composite_img.paste(img_sign, (470, 430), img_sign)

                # composite_img.show()
                composite_img.save(file_path.with_name(out_file_name))
                return composite_img

        except Exception as e:
            logger.debug(f"Error in opening file: {e}")
            return None

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', str(self.dir_path))
        logger.debug(f"Opening {fname[0]}")

        if fname[0]:
            pil_img = self.sign_pic(Path(fname[0]))
            if pil_img is None:
                return

            # Convert Pillow image to QPixmap
            pil_img_rgba = pil_img.convert("RGBA")
            data = pil_img_rgba.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_img_rgba.width, pil_img_rgba.height, QImage.Format_RGBA8888)
            qt_pixmap = QPixmap.fromImage(qimg)

            self.display_window.setPixmap(qt_pixmap)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())

