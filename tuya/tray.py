import json
import logging
import os
import pickle
import sys
from functools import partial

import tuyapy
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QColorDialog, QMenu, QSystemTrayIcon
from tuyapy import TuyaApi

PICKLED_SESSION_FILEPATH = ".tuya_session.dat"

logger = logging.getLogger(__name__)


class TuyaTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.counter = None

        self.devices = None
        self.device_ids = None
        self.lights = None
        self.switch = None
        self.scenes = None

        self.api = TuyaApi()

        self.setIcon(QIcon("img/icon-rounded.png"))
        self.setToolTip("TuyaTray")

        self.menu = QMenu()
        self.init_ui()

    @staticmethod
    def turn_off(device):
        logger.info(f"turning off device {device}")
        if not isinstance(device, list):
            return device.turn_off()
        else:
            return [i.turn_off() for i in device]

    @staticmethod
    def turn_on(device):
        logger.info(f"turning on device {device}")
        if not isinstance(device, list):
            return device.turn_on()
        else:
            return [i.turn_on() for i in device]

    @staticmethod
    def activate_scene(scene):
        logger.info(f"activating scene {scene}")
        scene.activate()

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
        if os.path.exists(PICKLED_SESSION_FILEPATH):
            logger.info(f"loading previous tuya session in {PICKLED_SESSION_FILEPATH}")
            with open(PICKLED_SESSION_FILEPATH, "rb") as pickle_file:
                tuyapy.tuyaapi.SESSION = pickle.load(pickle_file)
                pickle_file.close()
        else:
            logger.info(f"initializing new tuya api session")
            with open("config.json") as config_file:
                data = json.load(config_file)
                self.api.init(
                    username=data["username"],
                    password=data["password"],
                    countryCode=data["country_code"],
                    bizType=data["application"],
                )
                config_file.close()

            logger.info(f"saving tuya api session to disk {PICKLED_SESSION_FILEPATH}")
            with open(PICKLED_SESSION_FILEPATH, "wb") as pickle_file:
                pickle.dump(tuyapy.tuyaapi.SESSION, pickle_file)
                pickle_file.close()

        self.device_ids = self.api.get_all_devices()

        self.switch = dict(
            sorted(dict((i.name(), i) for i in self.device_ids if i.obj_type == "switch").items())
        )
        self.switch["All Switches"] = list(self.switch.values())
        logger.info(f"found {len(self.switch)} switches")

        self.lights = dict(
            sorted(dict((i.name(), i) for i in self.device_ids if i.obj_type == "light").items())
        )
        self.lights["All Lights"] = list(self.lights.values())
        logger.info(f"found {len(self.lights)} lights")

        self.scenes = dict(
            sorted(dict((i.name(), i) for i in self.device_ids if i.obj_type == "scene").items())
        )
        logger.info(f"found {len(self.scenes)} scenes")
        for scene_name, scene in self.scenes.items():
            logger.info(f"scene_name ({type(scene_name)}): {scene_name}")
            logger.info(f"scene ({type(scene)}): {scene}")

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

        self.menu.addSeparator()
        for scene_name, scene in self.scenes.items():
            # self.menus[f"{scene_name}_Action"] = self.menu.addMenu(scene_name)
            activate = self.menu.addAction(scene_name)
            activate.triggered.connect(partial(self.activate_scene, scene))

        self.menu.addSeparator()
        exit_action = self.menu.addAction("Exit")
        exit_action.triggered.connect(QCoreApplication.quit)
        self.setContextMenu(self.menu)

        logger.info("showing ui")
        self.show()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activated.connect(self.show_menu_on_trigger())

    def show_menu_on_trigger(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.contextMenu().popup(QCursor.pos())
