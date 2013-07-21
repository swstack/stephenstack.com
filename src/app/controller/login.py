"""
session.query(MyClass).\
    filter(MyClass.name == 'some name', MyClass.id > 5)
"""

from app.model.model import User
from contextlib import contextmanager
import json


class LoginManager(object):
    def __init__(self, database, resource_manager):
        self._resource_manager = resource_manager
        self.database = database
        self._client_secrets = None

    def _load_client_secrets(self):
        if not self._client_secrets:
            raw = open(self._resource_manager.\
                       get_fs_resource_path("client_secrets.json"), "r").read()
            self._client_secrets = json.loads(raw)

    def start(self):
        self._load_client_secrets()

    def get_client_id(self):
        return self._client_secrets["web"]["client_id"]

    @property
    @contextmanager
    def db(self):
        try:
            yield self.database.get_session()
        finally:
            pass

    def login(self, username, password):
        success = False
        with self.db as db:
            if db.query(User).filter(User.username == username,
                                     User.password == password):
                success = True
        return success

    def create_account(self, username, password):
        success = False
        with self.db as db:
            if db.query(User).filter(User.username == username):
                pass
            else:
                user = User()
                user.username = username
                user.password = password
                db.add(user)
                db.commit()
                success = True
        return success

    def get_users(self):
        db = self.database.get_session()
        return db.query(User).all()
