"""
session.query(MyClass).filter(MyClass.name == 'some name', MyClass.id > 5)
"""
import json


class LoginManager(object):
    def __init__(self, database, resource_manager):
        self._resource_manager = resource_manager
        self.database = database
        self._client_secrets = None

    def start(self):
        self._load_client_secrets()

    #================================================================================
    # Internal
    #================================================================================
    def _load_client_secrets(self):
        if not self._client_secrets:
            raw = open(self._resource_manager.\
                       get_fs_resource_path("client_secrets.json"), "r").read()
            self._client_secrets = json.loads(raw)

    #================================================================================
    # Public
    #================================================================================
    def get_client_id(self):
        return self._client_secrets["web"]["client_id"]

    def gplus_connect(self):
        pass
