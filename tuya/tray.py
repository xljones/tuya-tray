import json
import logging
import os
import pickle
from functools import partial

import tuyapy
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QColorDialog, QMenu, QSystemTrayIcon
from tuyapy import TuyaApi
from tuyapy.devices.climate import TuyaClimate
from tuyapy.devices.light import TuyaLight
from tuyapy.devices.scene import TuyaScene
from tuyapy.devices.switch import TuyaSwitch

PICKLED_SESSION_FILEPATH = ".tuya_session.dat"
TEMPERATURE_UNIT = "°C"

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
    def turn_off(device: TuyaSwitch | TuyaLight):
        logger.info(f"turning off device {device}")
        if not isinstance(device, list):
            return device.turn_off()
        else:
            return [i.turn_off() for i in device]

    @staticmethod
    def turn_on(device: TuyaSwitch | TuyaLight):
        logger.info(f"turning on device {device}")
        if not isinstance(device, list):
            return device.turn_on()
        else:
            return [i.turn_on() for i in device]

    @staticmethod
    def activate_scene(scene: TuyaScene):
        logger.info(f"activating scene {scene}")
        scene.activate()

    @staticmethod
    def change_colour(device: TuyaLight):
        colors = QColorDialog.getColor()
        h, s, v, t = colors.getHsv()
        s = int((s / 255 * 100))
        if s < 60:
            s = 60
        return device.set_color([h, s, 100])

    @staticmethod
    def incr_temp(device: TuyaClimate):
        current_temp = device.current_temperature()
        new_temp = current_temp + 1
        logger.info(f"increasing {device.name()} target temp from {current_temp} to {new_temp}")
        device.set_temperature(new_temp)

    @staticmethod
    def decr_temp(device: TuyaClimate):
        current_temp = device.current_temperature()
        new_temp = current_temp - 1
        logger.info(f"decreasing {device.name()} target temp from {current_temp} to {new_temp}")
        device.set_temperature(new_temp)

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

        self.devices = self.api.get_all_devices()
        for device in self.devices:
            logger.info(f"device: {device}")

        self.switches = {d.name(): d for d in self.devices if d.obj_type == "switch"}
        logger.info(f"found {len(self.switches)} switches")

        self.lights = {d.name(): d for d in self.devices if d.obj_type == "light"}
        logger.info(f"found {len(self.lights)} lights")

        self.scenes = {d.name(): d for d in self.devices if d.obj_type == "scene"}
        logger.info(f"found {len(self.scenes)} scenes")

        self.climates = {d.name(): d for d in self.devices if d.obj_type == "climate"}
        logger.info(f"found {len(self.climates)} climate controllers")

        for scene_name, scene in self.scenes.items():
            activate = self.menu.addAction(scene_name)
            activate.triggered.connect(partial(self.activate_scene, scene))
        self.menu.addSeparator()

        lights_menu = self.menu.addMenu("Lights")
        for device_name, device in self.lights.items():
            device_menu = lights_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(partial(self.turn_on, device))
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(partial(self.turn_off, device))
            change_color = device_menu.addAction("Light Color")
            change_color.triggered.connect(partial(self.change_colour, device))

        switches_menu = self.menu.addMenu("Switches")
        for device_name, device in self.switches.items():
            device_menu = switches_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(partial(self.turn_on, device))
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(partial(self.turn_off, device))

        climate_menu = self.menu.addMenu("Climate Controllers")
        for device_name, device in self.climates.items():
            logger.info(f"{device_name} data: {device.data}")
            device_menu = climate_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(partial(self.turn_on, device))
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(partial(self.turn_off, device))

            # show target and current temperatures of the climate controllers
            # target_temp = device_menu.addAction(f"Target: {device.target_temperature()}{TEMPERATURE_UNIT}")
            # target_temp.setDisabled(True)
            # current_temp = device_menu.addAction(f"Current: {device.current_temperature()}{TEMPERATURE_UNIT}")
            # current_temp.setDisabled(True)

            incr_temp = device_menu.addAction(f"+ 1{TEMPERATURE_UNIT}")
            incr_temp.triggered.connect(partial(self.incr_temp, device))
            decr_temp = device_menu.addAction(f"- 1{TEMPERATURE_UNIT}")
            decr_temp.triggered.connect(partial(self.decr_temp, device))

            # disable controls if the device is offline
            device_menu.setDisabled(not device.state())

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
