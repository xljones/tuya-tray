import logging

from tuyapy.devices import scene

logger = logging.getLogger(__name__)


class TuyaSceneExtended(scene.TuyaScene):
    def activate_scene(self):
        logger.info(f"activating scene {self.name()}")
        self.activate()
