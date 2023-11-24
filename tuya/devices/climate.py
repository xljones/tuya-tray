import logging

from tuyapy.devices import climate

logger = logging.getLogger(__name__)


class TuyaClimateExtended(climate.TuyaClimate):
    def incr_temp(self):
        current_temp = self.current_temperature()
        new_temp = current_temp + 1
        logger.info(f"increasing {self.name()} target temp from {current_temp} to {new_temp}")
        self.set_temperature(new_temp)

    def decr_temp(self):
        current_temp = self.current_temperature()
        new_temp = current_temp - 1
        logger.info(f"decreasing {self.name()} target temp from {current_temp} to {new_temp}")
        self.set_temperature(new_temp)
