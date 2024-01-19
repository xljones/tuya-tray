import logging
import sys

from PyQt6.QtWidgets import QApplication

from app.tuya.tray import TuyaTray

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    t = TuyaTray()
    t.show()

    app.exec()
