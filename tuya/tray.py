import logging
import os
import pickle

import tuyapy
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from tuyapy import TuyaApi
from tuyapy.devices import base

from tuya.config import Config
from tuya.const import PICKLED_SESSION_FILEPATH, TEMPERATURE_UNIT
from tuya.devices import (
    TuyaClimateExtended,
    TuyaLightExtended,
    TuyaSceneExtended,
    TuyaSwitchExtended,
)

from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TuyaTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        self.tuya_api: TuyaApi = TuyaApi()
        self.devices: List[Any] | None = None

        self.lights: Dict = dict()
        self.switches: Dict = dict()
        self.scenes: Dict = dict()
        self.scene_groups: Dict = {"other": {}}
        self.climates: Dict = dict()

        self.setIcon(QIcon("img/icon-rounded.png"))
        self.setToolTip("TuyaTray")

        self.menu = QMenu()

        self._load_session()
        self._init_ui()

    def _load_session(self, force_refresh: bool = False):
        config = Config()

        if os.path.exists(PICKLED_SESSION_FILEPATH) and not force_refresh:
            logger.info(f"loading previous tuya session in {PICKLED_SESSION_FILEPATH}")
            with open(PICKLED_SESSION_FILEPATH, "rb") as pickle_file:
                tuyapy.tuyaapi.SESSION = pickle.load(pickle_file)
                pickle_file.close()
        else:
            logger.info(f"initializing new tuya api session")
            self.tuya_api.init(
                username=config.username,
                password=config.password,
                countryCode=config.country_code,
                bizType=config.application,
            )

            logger.info(f"saving new tuya api session to disk {PICKLED_SESSION_FILEPATH}")
            with open(PICKLED_SESSION_FILEPATH, "wb") as pickle_file:
                pickle.dump(tuyapy.tuyaapi.SESSION, pickle_file)
                pickle_file.close()

        for scene_group_name in config.scene_groups:
            self.scene_groups.update({scene_group_name.lower(): {}})

        self.tuya_api.discover_devices()
        self.devices = self.tuya_api.get_all_devices()
        for device in self.devices:
            logger.info(f"device: {device}")

        device: base.TuyaDevice
        for device in self.devices:
            device_extended = device
            match device.object_type():
                case "switch":
                    device_extended.__class__ = TuyaSwitchExtended
                    self.switches.update({device.name(): device_extended})
                case "light":
                    device_extended.__class__ = TuyaLightExtended
                    self.lights.update({device.name(): device_extended})
                case "scene":
                    device_extended.__class__ = TuyaSceneExtended
                    self.scenes.update({device.name(): device_extended})
                    found_scene = False
                    for scene_name in self.scene_groups.keys():
                        if scene_name in device.name().lower():
                            found_scene = True
                            self.scene_groups[scene_name].update({device.name(): device_extended})
                    if found_scene is False:
                        self.scene_groups["other"].update({device.name(): device_extended})
                case "climate":
                    device_extended.__class__ = TuyaClimateExtended
                    self.climates.update({device.name(): device_extended})

        logger.info(f"found {len(self.switches)} switches")
        logger.info(f"found {len(self.lights)} lights")
        logger.info(f"found {len(self.scenes)} scenes")
        logger.info(f"found {len(self.scene_groups)} scene_groups")
        logger.info(f"found {len(self.climates)} climate controllers")

    def _init_ui(self):
        for _, scene_group_devices in self.scene_groups.items():
            for scene_name, scene in scene_group_devices.items():
                activate = self.menu.addAction(scene_name)
                activate.triggered.connect(scene.activate_scene)
            self.menu.addSeparator()

        lights_menu = self.menu.addMenu("Lights")
        for device_name, device in self.lights.items():
            device_menu = lights_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(device.turn_on)
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(device.turn_off)
            change_color = device_menu.addAction("Light Color")
            change_color.triggered.connect(device.change_colour)

        switches_menu = self.menu.addMenu("Switches")
        for device_name, device in self.switches.items():
            device_menu = switches_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(device.turn_on)
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(device.turn_off)

        climate_menu = self.menu.addMenu("Climate Controllers")
        for device_name, device in self.climates.items():
            device_menu = climate_menu.addMenu(device_name)
            device_on = device_menu.addAction("On")
            device_on.triggered.connect(device.turn_on)
            device_off = device_menu.addAction("Off")
            device_off.triggered.connect(device.turn_off)

            # show target and current temperatures of the climate controllers
            # target_temp = device_menu.addAction(f"Target: {device.target_temperature()}{TEMPERATURE_UNIT}")
            # target_temp.setDisabled(True)
            # current_temp = device_menu.addAction(f"Current: {device.current_temperature()}{TEMPERATURE_UNIT}")
            # current_temp.setDisabled(True)

            incr_temp = device_menu.addAction(f"+ 1{TEMPERATURE_UNIT}")
            incr_temp.triggered.connect(device.incr_temp)
            decr_temp = device_menu.addAction(f"- 1{TEMPERATURE_UNIT}")
            decr_temp.triggered.connect(device.decr_temp)

            # disable controls if the device is offline
            # device_menu.setDisabled(not device.state())

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
