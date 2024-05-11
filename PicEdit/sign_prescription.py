from io import open_code
import sys
from pathlib import Path
from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QFileDialog, QWidget
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QAction, QPixmap


class MyApp(QMainWindow):

    def __init__(self):
        self.file_path = Path('원외처방-차트번호5263_1.jpg')
        super().__init__()
        self.initUI()

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
        out_file_name = Path('OUT_' + file_path.name)

        try:
            # Open an Image
            with Image.open(file_path) as base_img:
                img_sign = Image.open('jye_sign.png')

                composite_img = base_img.copy()
                composite_img.paste(img_sign, (470, 430), img_sign)

                # composite_img.show()
                composite_img.save(out_file_name.with_suffix('.png'))
                return composite_img

        except Exception as e:
            print("Error in opening the file")
            print(e)
            return None

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', './')

        if fname[0]:
            pillow_image = self.sign_pic(Path(fname[0]))
            if pillow_image is None:
                return

            # Convert Pillow image to QPixmap
            qt_image = QPixmap(pillow_image.size[0], pillow_image.size[1])
            qt_image.fill(0)
            qt_pixmap = QPixmap(qt_image)
            qt_pixmap.loadFromData(pillow_image.tobytes(), "png")

            # Create a QLabel to display the image
            self.display_window.setPixmap(qt_pixmap)
            widget1 = QWidget()
            label = QLabel()
            label.setPixmap(QPixmap(self.file_path))
            label.show()

            # f = open(fname[0], 'r')
            #
            # with f:
            #     data = f.read()
            #     self.textEdit.setText(data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())




# # Call draw method to add 2D graphic in an image
# final_img = ImageDraw.Draw(base_img)
# # Custom font style and font size
# my_font = ImageFont.truetype('FreeMono.ttf', 65)
# # Add text to an image
# final_img.text((500, 500), "nice care", font=my_font, fill=(255, 0, 0))
# # Display edited image
# base_img.show()
