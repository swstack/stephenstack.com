from app.model.model import Base, Resume, User, Message
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
import heapq


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
        return session_db.query(Resume).order_by(Resume.datetime_uploaded.desc())

    def _get_my_user(self):
        session_db = self.get_session()
        the_great_and_powerful = \
            session_db.query(User).filter(User.gapi_id == "110649862410112880601")[0]
        return the_great_and_powerful

    def _merge_conversations(self, convo_a, convo_b):
        if len(convo_a) < 1:
            result = convo_b

        elif len(convo_b) < 1:
            result = convo_a
        else:
            result = []
            i, j = 0, 0
            while i < len(convo_a) and j < len(convo_b):
                if convo_a[i].datetime_sent <= convo_b[j].datetime_sent:
                    result.append(convo_a[i])
                    i += 1
                else:
                    result.append(convo_b[j])
                    j += 1
        return result

    #================================================================================
    # Public
    #================================================================================
    def get_session(self):
        return self.session()

    def get_user(self, uid):
        session_db = self.get_session()
        return session_db.query(User).filter(User.id == uid).all()[0]

    def get_conversation(self, gapi_id):
        session_db = self.get_session()
        me = self._get_my_user()
        user = session_db.query(User).filter(User.gapi_id == gapi_id).all()[0]

        # get all messages sent by me, to this person, ordered from oldest to newest
        msgs_me = session_db.query(Message).filter(Message.sender == me.id,
                                                   Message.receiver == user.id).\
                                            order_by(Message.datetime_sent.asc()).\
                                all()

        # get all messages sent by this person, to me, ordered from oldest to newest
        msgs_user = session_db.query(Message).filter(Message.sender == user.id,
                                                     Message.receiver == me.id).\
                                              order_by(Message.datetime_sent.asc()).\
                                all()

        # merge
        merged_messages = self._merge_conversations(msgs_me, msgs_user)

        # jsonify the messages
        merged_messages = [msg.to_json() for msg in merged_messages]

        # replace sender/receiver id's with jsonified users
        for json_msg in merged_messages:
            sender_id = json_msg["sender"]
            json_msg["sender"] = self.get_user(sender_id).to_json()

            receiver_id = json_msg["receiver"]
            json_msg["receiver"] = self.get_user(receiver_id).to_json()

        return merged_messages

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
