import json
from typing import List

from tuya.const import CONFIG_FILEPATH


class BadConfigException(Exception):
    pass


class Config:
    def __init__(self, config_filename: str | None = CONFIG_FILEPATH) -> None:
        self.username: str | None = None
        self.password: str | None = None
        self.country_code: str | None = None
        self.application: str | None = None
        self.scene_group_names: List[str] = []

        if config_filename is not None:
            self._load_from_file(config_filename=config_filename)
            self._verify()

    def _load_from_file(self, config_filename: str) -> None:
        with open(config_filename) as config_file:
            config_data = json.load(config_file)
            self.username = config_data.get("username")
            self.password = config_data.get("password")
            self.country_code = config_data.get("country_code")
            self.application = config_data.get("application")
            self.scene_group_names = config_data.get("scene_group_names", [])
            config_file.close()

    def _verify(self) -> None:
        applications_allowed = sorted({"smart_life", "tuya"})

        issues = []
        if not self.username:
            issues.append("missing username")
        if not self.password:
            issues.append("missing password")
        if not self.country_code:
            issues.append("missing country code")
        if self.application not in applications_allowed:
            issues.append(
                f"application type '{self.application}' is not valid. must be one of {', '.join(applications_allowed)}"
            )

        if issues:
            raise BadConfigException(", ".join(issues))
