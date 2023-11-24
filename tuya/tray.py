import json
import sys
from functools import partial

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon, QCursor
from PyQt6.QtWidgets import QApplication, QColorDialog, QMenu, QSystemTrayIcon
from tuyapy import TuyaApi

api = TuyaApi()


class TuyaTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.counter = None
        self.menus = None

        self.devices = None
        self.device_ids = None
        self.lights = None
        self.switch = None
        self.scenes = None

        self.setIcon(QIcon("img/icon-rounded.png"))
        self.setToolTip("TuyaTray")

        self.menu = QMenu()
        self.init_ui()

    @staticmethod
    def turn_off(device):
        if not isinstance(device, list):
            return device.turn_off()
        else:
            return [i.turn_off() for i in device]

    @staticmethod
    def turn_on(device):
        if not isinstance(device, list):
            return device.turn_on()
        else:
            return [i.turn_on() for i in device]

    @staticmethod
    def change_colour(device):
        colors = QColorDialog.getColor()
        h, s, v, t = colors.getHsv()
        s = int((s / 255 * 100))
        if s < 60:
            s = 60
        if not isinstance(device, list):
            return device.set_color([h, s, 100])
        else:
            return [i.set_color([h, s, 100]) for i in device]

    def init_ui(self):
        with open("config.json") as config:
            data = json.load(config)

        print(data)
        api.init(
            data["username"],
            data["password"],
            data["country_code"],
            data["application"],
        )

        self.device_ids = api.get_all_devices()
        print(self.device_ids)

        self.switch = dict(sorted(dict((i.name(), i) for i in self.device_ids if i.obj_type == "switch").items()))
        self.switch["All Switches"] = list(self.switch.values())
        self.lights = dict(sorted(dict((i.name(), i) for i in self.device_ids if i.obj_type == "light").items()))
        self.lights["All Lights"] = list(self.lights.values())
        self.devices = {**self.switch, **self.lights}
        self.menus = dict()
        self.counter = 0

        for j in self.devices.keys():
            if isinstance(self.devices[j], list) is False and self.devices[j].obj_type == "light":
                if self.counter == 0:
                    self.menu.addSeparator()
                    self.counter += 1
            self.menus[f"{j}_Action"] = self.menu.addMenu(j)
            if j in self.lights.keys():
                on_menu = self.menus[f"{j}_Action"].addMenu("On")
                on = on_menu.addAction("On")
                colour_wheel = on_menu.addAction("Light Colour")
                colour_wheel.triggered.connect(partial(self.change_colour, self.devices[j]))
            else:
                on = self.menus[f"{j}_Action"].addAction("On")

            off = self.menus[f"{j}_Action"].addAction("Off")
            on.triggered.connect(partial(self.turn_on, self.devices[j]))
            off.triggered.connect(partial(self.turn_off, self.devices[j]))

        exit_action = self.menu.addAction("Exit")
        exit_action.triggered.connect(QCoreApplication.quit)
        self.setContextMenu(self.menu)
        print("showing ui")
        self.show()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activated.connect(self.show_menu_on_trigger())

    def show_menu_on_trigger(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.contextMenu().popup(QCursor.pos())
