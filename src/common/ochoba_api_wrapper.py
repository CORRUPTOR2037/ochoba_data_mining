from os import environ
from requests_toolbelt import sessions


class OchobaApiWrapper:
    def __init__(self, config):
        self.url = config["url"]
        self.session = sessions.BaseUrlSession(base_url=self.url)
        if "token" in config:
            self.session.headers.update({"X-Device-Token": config["token"]})
        else:
            self.session.headers.update({"X-Device-Token": config['environ']})
        self.min_delay = 1

    def execute(self, endpoint):
        return self.session.get(endpoint)
