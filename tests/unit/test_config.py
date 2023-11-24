from parameterized import parameterized

from tuya.config import Config


class TestConfig:
    def test_load(self):
        c = Config()
        c.load_from_file("tests/fixtures/sample_config.json")
        assert c.username == "user@test.com"
        assert c.password == "my_password_123"
        assert c.country_code == "44"
        assert c.application == "smart_life"

    @parameterized.expand(
        [
            [
                "bad username",
                {
                    "username": "",
                    "password": "def",
                    "country_code": "00",
                    "application": "smart_life",
                },
                ["missing username"],
            ],
            [
                "bad password",
                {
                    "username": "abc",
                    "password": "",
                    "country_code": "00",
                    "application": "smart_life",
                },
                ["missing password"],
            ],
            [
                "bad country code",
                {
                    "username": "abc",
                    "password": "def",
                    "country_code": "",
                    "application": "smart_life",
                },
                ["missing country code"],
            ],
            [
                "bad application",
                {
                    "username": "abc",
                    "password": "def",
                    "country_code": "00",
                    "application": "toyota",
                },
                ["application type 'toyota' is not valid. must be one of smart_life, tuya"],
            ],
        ]
    )
    def test_verify(self, _, test_config, expected_issues):
        c = Config()
        c.username = test_config["username"]
        c.password = test_config["password"]
        c.country_code = test_config["country_code"]
        c.application = test_config["application"]
        v = c.verify()
        assert v == expected_issues, f"expected '{v}' == '{expected_issues}'"