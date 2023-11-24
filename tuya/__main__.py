import sys

from PyQt6.QtWidgets import QApplication

from tuya import config, tray

if __name__ == "__main__":
    c = config.Config()
    c.load_from_file()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    t = tray.TuyaTray()
    t.show()

    app.exec()
