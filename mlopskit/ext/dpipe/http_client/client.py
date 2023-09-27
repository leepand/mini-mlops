import functools
import requests
import urllib.parse
import json


class SDK:
    def __init__(self, host: str):
        self.host = host

    @functools.lru_cache(maxsize=None)
    def session(self):
        s = requests.Session()
        return s

    def request(self, method, endpoint, as_json=True, session=None, **kwargs):
        r = (session or self.session()).request(
            method=method, url=urllib.parse.urljoin(self.host, endpoint), **kwargs
        )
        r.raise_for_status()
        return (
            r.json()
            if as_json and r.headers.get("content-type") == "application/json"
            else r
        )

    def get(self, endpoint, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self.request("PUT", endpoint, **kwargs)


class DpipeClient(SDK):
    def create(self, name: str, protocol: str, url: str):
        """Create a message bus."""
        self.post(
            "/api/message-bus/",
            json={"name": name, "protocol": protocol, "url": url},
        )
        return self(name)

    def list(self):
        """List existing message buses."""
        return self.get("/api/message-bus/")

    def __call__(self, git_bus_name: str):
        """Choose an existing message bus."""
        return GitBus(host=self.host, name=git_bus_name)


class GitBus(SDK):
    def __init__(self, host, name):
        super().__init__(host)
        self.name = name

    def send(self, topic, key, value):
        self.post(
            f"/api/git-bus/{self.name}",
            json={"topic": topic, "key": str(key), "value": json.dumps(value)},
        )

    def pipes(self, name=None, version=None, profile=None):
        resp = self.get(
            f"/api/git-bus/{self.name}/pipes",
            params={"version": version, "name": name, "profile": profile},
        )
        return resp

    def delete(self):
        return self.request("DELETE", f"/api/git-bus/{self.name}", as_json=False)

    def exists(self, file_or_dir):
        return self.get(
            f"/api/git-bus/{self.name}/file_exists",
            params={"file_or_dir": file_or_dir},
        )

    def listdir_attr(self, file_or_dir, name, version, profile):
        resp = self.get(
            f"/api/git-bus/{self.name}/listdir_attr",
            params={
                "file_or_dir": file_or_dir,
                "name": name,
                "version": version,
                "profile": profile,
            },
        )
        return resp
