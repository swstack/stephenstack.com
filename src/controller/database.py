from model.model import Base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
from util.paths import STORE_DIR


class Database(object):

    db_string = "sqlite:////%s/wamcsim.db" % STORE_DIR

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
        print self.db_string
        self.create_db_if_needed()
