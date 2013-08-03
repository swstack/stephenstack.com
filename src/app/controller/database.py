from app.model.model import Base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker


class Database(object):
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.engine = None
        self.session = None
        self.db_string = None

    def start(self):
        db_dir_path = self.resource_manager.get_fs_resource_path("store")
        self.db_string = "sqlite:///%s/app.db" % db_dir_path
        self.engine = create_engine(self.db_string)
        self.session = scoped_session(sessionmaker(bind=self.engine,
                                                   autocommit=False,
                                                   autoflush=True))
        Base.metadata.create_all(self.engine)

    #================================================================================
    # Public
    #================================================================================
    def get_session(self):
        return self.session()
