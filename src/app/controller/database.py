from model.model import Base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
import os

STORE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "store"))


class Database(object):

    db_string = "sqlite:////%s/store.db" % STORE_DIR

    def __init__(self):
        self.engine = None
        self.session = None

    def create_db_if_needed(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.session()

    def start(self):
        self.engine = create_engine(self.db_string)
        self.session = scoped_session(sessionmaker(bind=self.engine,
                                                   autocommit=False,
                                                   autoflush=True))
        self.create_db_if_needed()
