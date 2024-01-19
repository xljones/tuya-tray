import logging

from PyQt6.QtWidgets import QColorDialog
from tuyapy.devices import light

logger = logging.getLogger(__name__)


class TuyaLightExtended(light.TuyaLight):
    def change_colour(self):
        colors = QColorDialog.getColor()
        h, s, v, t = colors.getHsv()
        s = int((s / 255 * 100))
        if s < 60:
            s = 60
        return self.set_color([h, s, 100])
