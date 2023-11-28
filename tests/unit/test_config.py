import pytest
from parameterized import parameterized

from tuya.config import BadConfigException, Config


class TestConfig:
    def test__load_config_from_file(self):
        c = Config(config_filename="tests/fixtures/sample_config.json")

        assert c.username == "user@test.com"
        assert c.password == "my_password_123"
        assert c.country_code == "44"
        assert c.application == "smart_life"

    @parameterized.expand(
        [
            [
                "valid config",
                {
                    "username": "abc@me.com",
                    "password": "defabc",
                    "country_code": "44",
                    "application": "smart_life",
                },
                None,
            ],
            [
                "bad username",
                {
                    "username": "",
                    "password": "def",
                    "country_code": "00",
                    "application": "smart_life",
                },
                "missing username",
            ],
            [
                "bad password",
                {
                    "username": "abc",
                    "password": "",
                    "country_code": "00",
                    "application": "smart_life",
                },
                "missing password",
            ],
            [
                "bad country code",
                {
                    "username": "abc",
                    "password": "def",
                    "country_code": "",
                    "application": "smart_life",
                },
                "missing country code",
            ],
            [
                "bad application",
                {
                    "username": "abc",
                    "password": "def",
                    "country_code": "00",
                    "application": "toyota",
                },
                "application type 'toyota' is not valid. must be one of smart_life, tuya",
            ],
        ]
    )
    def test_verify(self, test_name: str, test_config: dict, expected_exception_str: str):
        c = Config()
        c.username = test_config["username"]
        c.password = test_config["password"]
        c.country_code = test_config["country_code"]
        c.application = test_config["application"]

        if expected_exception_str:
            with pytest.raises(expected_exception=BadConfigException, match=expected_exception_str):
                c._verify()
        else:
            c._verify()
