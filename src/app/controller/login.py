"""
session.query(MyClass).\
    filter(MyClass.name == 'some name', MyClass.id > 5)
"""

from contextlib import contextmanager
from model.model import User


class LoginManager(object):
    def __init__(self, database):
        self.database = database

    def start(self):
        pass

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
