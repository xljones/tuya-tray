import json

class Config():
    def __init__(self):
        self.username = None
        self.password = None
        self.country_code = None
        self.application = None

    def load_from_file(self, filename="config.json"):
        with open(filename) as config:
            data = json.load(config)
            self.username = data['username']
            self.password = data['password']
            self.country_code = data['country_code']
            self.application = data['application']
        self.verify()

    def verify(self):
        application_allowed = ["smart_life", "tuya"]

        issues = []
        if not self.username:
            issues.append("missing username")
        if not self.password:
            issues.append("missing password")
        if not self.country_code:
            issues.append("missing country code")
        if self.application not in application_allowed:
            issues.append(f"application type '{self.application}' is not valid. must be one of {', '.join(application_allowed)}")

        return issues
