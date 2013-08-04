from app.model.model import Base, Resume
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
    # Internal
    #================================================================================
    def _resumes_newest_to_oldest(self):
        session_db = self.get_session()
        return session_db.query(Resume).order_by(Resume.date_uploaded.desc())

    #================================================================================
    # Public
    #================================================================================
    def get_session(self):
        return self.session()

    def get_most_recent_pdf_resume(self):
        resumes_newest_to_oldest = self._resumes_newest_to_oldest()
        for resume in resumes_newest_to_oldest:
            if resume.filetype == "pdf":
                return resume

    def get_most_recent_docx_resume(self):
        resumes_newest_to_oldest = self._resumes_newest_to_oldest()
        for resume in resumes_newest_to_oldest:
            if resume.filetype == "docx":
                return resume
