import logging

from tuyapy.devices import switch

logger = logging.getLogger(__name__)


class TuyaSwitchExtended(switch.TuyaSwitch):
    def __init__(self):
        super().__init__()
