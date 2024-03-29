import logging
import os
import pickle
from typing import Any, Dict, List, Union

import tuyapy
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from tuyapy import TuyaApi
from tuyapy.devices import base

from app.config import Config
from app.const import (
    PICKLED_SESSION_FILEPATH,
    TEMPERATURE_UNIT,
    ExtraAbilities,
)
from app.devices import (
    TuyaClimateExtended,
    TuyaLightExtended,
    TuyaSceneExtended,
    TuyaSwitchExtended,
)
from app.exceptions import DeviceAbilityNotFound

logger = logging.getLogger(__name__)


class TuyaTray(QSystemTrayIcon):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.tuya_api: TuyaApi = TuyaApi()
        self.devices: List[Any] = []

        self.lights: Dict = dict()
        self.switches: Dict = dict()
        self.scenes: Dict = dict()
        self.scene_groups: Dict = {"other": {}}
        self.climates: Dict = dict()

        self.setIcon(QIcon("app/img/icon-rounded.png"))
        self.setToolTip("TuyaTray")

        self.menu = QMenu()

        self._load_session()
        self._init_ui()

    def _load_session(self, force_refresh: bool = False) -> None:
        config = Config()

        if os.path.exists(PICKLED_SESSION_FILEPATH) and not force_refresh:
            logger.info(
                f"loading previous tuya session in {PICKLED_SESSION_FILEPATH}"
            )
            with open(PICKLED_SESSION_FILEPATH, "rb") as pickle_file:
                tuyapy.tuyaapi.SESSION = pickle.load(pickle_file)
                pickle_file.close()
        else:
            logger.info("initializing new tuya api session")
            self.tuya_api.init(
                username=config.username,
                password=config.password,
                countryCode=config.country_code,
                bizType=config.application,
            )

            logger.info(
                "saving new tuya api session "
                f"to disk {PICKLED_SESSION_FILEPATH}"
            )
            with open(PICKLED_SESSION_FILEPATH, "wb") as pickle_file:
                pickle.dump(tuyapy.tuyaapi.SESSION, pickle_file)
                pickle_file.close()

        for scene_group_name in config.scene_group_names:
            self.scene_groups.update({scene_group_name.lower(): {}})

        self.tuya_api.discover_devices()
        self.devices = self.tuya_api.get_all_devices()

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
                            self.scene_groups[scene_name].update(
                                {device.name(): device_extended}
                            )
                    if found_scene is False:
                        self.scene_groups["other"].update(
                            {device.name(): device_extended}
                        )
                case "climate":
                    device_extended.__class__ = TuyaClimateExtended
                    self.climates.update({device.name(): device_extended})

        logger.info(f"found {len(self.switches)} switches")
        logger.info(f"found {len(self.lights)} lights")
        logger.info(f"found {len(self.scenes)} scenes")
        logger.info(f"found {len(self.scene_groups)} scene_groups")
        logger.info(f"found {len(self.climates)} climate controllers")

    @staticmethod
    def _add_device_to_menu(
        root_menu: QMenu,
        device: Union[
            TuyaClimateExtended, TuyaLightExtended, TuyaSwitchExtended
        ],
        device_name: str,
        extra_abilities: List = [],
    ) -> None:
        device_menu = root_menu.addMenu(device_name)
        device_on = device_menu.addAction("On")
        device_on.triggered.connect(  # type: ignore[attr-defined]
            device.turn_on,
        )
        device_off = device_menu.addAction("Off")
        device_off.triggered.connect(  # type: ignore[attr-defined]
            device.turn_off,
        )

        for extra_ability in extra_abilities:
            match extra_ability:
                case ExtraAbilities.CHANGE_COLOR:
                    cc = device_menu.addAction("Light Color")
                    cc.triggered.connect(  # type: ignore[attr-defined]
                        device.change_colour,
                    )
                case ExtraAbilities.CLIMATE_CONTROL:
                    # show target and current temperatures of the
                    # climate controllers
                    target_temp = device_menu.addAction(
                        f"Target: {device.target_temperature()}"
                        f"{TEMPERATURE_UNIT}"
                    )
                    target_temp.setDisabled(True)
                    current_temp = device_menu.addAction(
                        f"Current: {device.current_temperature()}"
                        f"{TEMPERATURE_UNIT}"
                    )
                    current_temp.setDisabled(True)

                    incr_temp = device_menu.addAction(f"+ 1{TEMPERATURE_UNIT}")
                    incr_temp.triggered.connect(  # type: ignore[attr-defined]
                        device.incr_temp,
                    )
                    decr_temp = device_menu.addAction(f"- 1{TEMPERATURE_UNIT}")
                    decr_temp.triggered.connect(  # type: ignore[attr-defined]
                        device.decr_temp,
                    )
                case _:
                    raise DeviceAbilityNotFound(
                        f"{extra_ability} is not implemented"
                    )

    def _init_ui(self) -> None:
        for _, scene_group_devices in self.scene_groups.items():
            for scene_name, scene in scene_group_devices.items():
                activate = self.menu.addAction(scene_name)
                activate.triggered.connect(scene.activate_scene)
            self.menu.addSeparator()

        lights_menu = self.menu.addMenu("Lights")
        switches_menu = self.menu.addMenu("Switches")
        climate_menu = self.menu.addMenu("Climate Controllers")

        for device_name, device in self.lights.items():
            self._add_device_to_menu(
                root_menu=lights_menu,
                device=device,
                device_name=device_name,
                extra_abilities=[ExtraAbilities.CHANGE_COLOR],
            )

        for device_name, device in self.switches.items():
            self._add_device_to_menu(
                root_menu=switches_menu,
                device=device,
                device_name=device_name,
            )

        for device_name, device in self.climates.items():
            self._add_device_to_menu(
                root_menu=climate_menu,
                device=device,
                device_name=device_name,
                extra_abilities=[ExtraAbilities.CLIMATE_CONTROL],
            )

        self.menu.addSeparator()
        exit_action = self.menu.addAction("Exit")
        exit_action.triggered.connect(  # type: ignore[attr-defined]
            QCoreApplication.quit,
        )
        self.setContextMenu(self.menu)

        logger.info("showing ui")
        self.show()
