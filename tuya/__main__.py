import sys
import logging

from PyQt6.QtWidgets import QApplication

from tuya.config import Config
from tuya.tray import TuyaTray

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

if __name__ == "__main__":
    c = Config()
    c.load_from_file()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    t = TuyaTray()
    t.show()

    app.exec()
