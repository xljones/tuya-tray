import logging
import os
import pickle
from datetime import datetime
from typing import Any, Dict, List

import tuyapy
from PyQt6.QtCore import QCoreApplication, QObject
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
from app.helpers import pretty_date

logger = logging.getLogger(__name__)


class TuyaTray(QSystemTrayIcon):
    def __init__(
        self,
        parent: QObject,
    ) -> None:
        super().__init__(parent=parent)

        self.tuya_api: TuyaApi = TuyaApi()
        self.devices: List[Any] = []

        self.lights: Dict = dict()
        self.switches: Dict = dict()
        self.scenes: Dict = dict()
        self.scene_groups: Dict = {"other": {}}
        self.climates: Dict = dict()

        self.menu: QMenu = QMenu()
        self.lights_menu: QMenu | None = None
        self.switches_menu: QMenu | None = None
        self.climate_menu: QMenu | None = None

        self.last_updated: datetime | None = None

        self._load_session()
        self._init_ui()

        # show the Tray App
        self.setIcon(QIcon("app/img/icon-rounded.png"))
        self.setToolTip("TuyaTray")
        self.setContextMenu(self.menu)

    def _load_session(self, force_refresh: bool = False) -> None:
        config = Config()

        if os.path.exists(PICKLED_SESSION_FILEPATH) and not force_refresh:
            logger.info(
                "loading previous tuya session "
                f"from {PICKLED_SESSION_FILEPATH}"
            )
            with open(PICKLED_SESSION_FILEPATH, "rb") as pickle_file:
                tuyapy.tuyaapi.SESSION = pickle.load(pickle_file)
                self.last_updated = pickle.load(pickle_file)
                pickle_file.close()
        else:
            if force_refresh:
                logger.info("refreshing devices using old credentials")
                response_payload = self.tuya_api.discover_devices()
                if response_payload:
                    self.last_updated = datetime.now()
                else:
                    return
            else:
                logger.info("initializing new tuya api session")
                self.tuya_api.init(
                    username=config.username,
                    password=config.password,
                    countryCode=config.country_code,
                    bizType=config.application,
                )
                self.last_updated = datetime.now()

            logger.info(
                "saving tuya api session "
                f"to disk {PICKLED_SESSION_FILEPATH}"
            )
            with open(PICKLED_SESSION_FILEPATH, "wb") as pickle_file:
                pickle.dump(tuyapy.tuyaapi.SESSION, pickle_file)
                pickle.dump(self.last_updated, pickle_file)
                pickle_file.close()

        for scene_group_name in config.scene_group_names:
            self.scene_groups.update({scene_group_name.lower(): {}})

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

        logger.debug(f"found {len(self.switches)} switches")
        logger.debug(f"found {len(self.lights)} lights")
        logger.debug(f"found {len(self.scenes)} scenes")
        logger.debug(f"found {len(self.scene_groups)} scene_groups")
        logger.debug(f"found {len(self.climates)} climate controllers")

    @staticmethod
    def _add_device_to_menu(
        root_menu: QMenu,
        device: TuyaClimateExtended | TuyaLightExtended | TuyaSwitchExtended,
        device_name: str,
        extra_abilities: List = [],
    ) -> None:
        device_menu = root_menu.addMenu(device_name)
        device_state = device_menu.addAction(
            f"State: {'On' if device.state() else 'Off'}"
        )
        device_state.setDisabled(True)
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

    def _handle_tray_icon_clicked(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        logger.info("handling tray icon click")
        self._load_session(force_refresh=True)
        self._init_ui()
        logger.info(f"last updated={self._get_time_since_update()}")
        self.last_updated_action.setText(self._get_time_since_update())

    def _get_time_since_update(self) -> str:
        if self.last_updated is None:
            return "updated ∞ ago"
        return "updated " + pretty_date(datetime.now() - self.last_updated)

    def _debug(self) -> None:
        import pdb

        pdb.set_trace()

    def _init_ui(self) -> None:
        self.menu.clear()

        for _, scene_group_devices in self.scene_groups.items():
            for scene_name, scene in scene_group_devices.items():
                activate = self.menu.addAction(scene_name)
                activate.triggered.connect(scene.activate_scene)
            self.menu.addSeparator()

        self.lights_menu = self.menu.addMenu("Lights")
        self.switches_menu = self.menu.addMenu("Switches")
        self.climate_menu = self.menu.addMenu("Climate Controllers")

        for device_name, device in self.lights.items():
            self._add_device_to_menu(
                root_menu=self.lights_menu,
                device=device,
                device_name=device_name,
                extra_abilities=[ExtraAbilities.CHANGE_COLOR],
            )

        for device_name, device in self.switches.items():
            self._add_device_to_menu(
                root_menu=self.switches_menu,
                device=device,
                device_name=device_name,
            )

        for device_name, device in self.climates.items():
            self._add_device_to_menu(
                root_menu=self.climate_menu,
                device=device,
                device_name=device_name,
                extra_abilities=[ExtraAbilities.CLIMATE_CONTROL],
            )

        self.menu.addSeparator()
        self.last_updated_action = self.menu.addAction(
            self._get_time_since_update()
        )
        self.last_updated_action.setDisabled(True)
        debug_action = self.menu.addAction("Debug")
        debug_action.triggered.connect(self._debug)  # type: ignore[attr-defined]
        exit_action = self.menu.addAction("Exit")
        exit_action.triggered.connect(  # type: ignore[attr-defined]
            QCoreApplication.quit,
        )

        self.activated.connect(self._handle_tray_icon_clicked)  # type: ignore[attr-defined]
