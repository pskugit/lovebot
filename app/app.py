import os
import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui

from src.cmd.swiper import main as swiper
from src.cmd.texter import main as texter

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.run_swiper_btn = QtWidgets.QPushButton("Run Swiper!")
        self.run_texter_btn = QtWidgets.QPushButton("Run Texter!")

        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.run_swiper_btn)
        self.layout.addWidget(self.run_texter_btn)

        self.run_swiper_btn.clicked.connect(self.run_swiper)
        self.run_texter_btn.clicked.connect(self.run_texter)

    @QtCore.Slot()
    def run_swiper(self):
        swiper()
    
    @QtCore.Slot()
    def run_texter(self):
        texter()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())