from tuya_tray import TuyaTray
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    if not QApplication.instance():  # create QApplication if it doesn't exist
        print("QApplication no instance, launching app")
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        tray = TuyaTray()
        tray.show()

        app.exec()

    exit(1)
