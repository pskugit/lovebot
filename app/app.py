import os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader

from src.cmd.update_backlog import main as update_backlog
from src.cmd.swiper import main as swiper
from src.cmd.texter import main as texter
from src.cmd.login import main as login

from dotenv import load_dotenv
import configparser

load_dotenv()
config = configparser.ConfigParser()
config.read(os.environ["LOVEBOT_CONFIG"])
loader = QUiLoader()
path_prefix = config['DEFAULT']["PathPrefix"]

class MyApp(QtWidgets.QApplication):
    def __init__(self):
        super().__init__()
        self.ui = loader.load(path_prefix+"assets/lovebot.ui", None)
        self.ui_setup()
        self.connection_setup()
    
    @QtCore.Slot()
    def run_update_backlog(self):
        update_backlog()

    @QtCore.Slot()
    def run_swiper(self):
        #self.ui.status_label.setText("I'm swiping...")
        run_report = swiper()
        self.ui.status_label.setText(run_report)

    @QtCore.Slot()
    def run_texter(self):
        #self.ui.status_label.setText("I'm texting...")
        run_report = texter()
        self.ui.status_label.setText(run_report)

    @QtCore.Slot()
    def run_login(self):
        login()
        self.ui.status_label.setText("Alright, let's go!")

    def ui_setup(self):
        #central_image
        pixmap = QtGui.QPixmap(path_prefix+"assets/logo_small_centered.png")
        self.ui.central_image.setPixmap(pixmap)
        #favicon
        my_icon = QtGui.QIcon()
        my_icon.addFile(path_prefix+"assets/favicon.ico")
        self.ui.setWindowIcon(my_icon)

    def connection_setup(self):
        self.ui.swipe_btn.clicked.connect(self.run_swiper)
        self.ui.text_btn.clicked.connect(self.run_texter)
        self.ui.login_btn.clicked.connect(self.run_login)


if __name__ == "__main__":
    app = MyApp()
    app.ui.show()
    app.exec()