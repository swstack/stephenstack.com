from model.model import User


class LoginManager(object):
    def __init__(self, database):
        self.database = database

    def start(self):
        pass

    def login(self, username, password):
        db = self.database.get_session()
        user = User()
        user.username = username
        user.password = password
        db.add(user)
        db.commit()

    def get_users(self):
        db = self.database.get_session()
        return db.query(User).all()
