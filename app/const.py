from enum import Enum

PICKLED_SESSION_FILEPATH = ".tuya_session.dat"
CONFIG_FILEPATH = ".config.json"
TEMPERATURE_UNIT = "°C"


class ExtraAbilities(Enum):
    CHANGE_COLOR = 1
    CLIMATE_CONTROL = 2
