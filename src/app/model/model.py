from sqlalchemy import Column, Integer, String, Enum, DateTime, LargeBinary
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.schema import ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    gapi_id = Column(Integer)
    name = Column(String)
    thumbnail_url = Column(String)
    profile_pic_url = Column(String)

    def __repr__(self):
        return "<User(%s : %s)>" % (self.id, self.name)


class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer, primary_key=True)
    file = Column(LargeBinary)
    filename = Column(String)
    filetype = Column(Enum("pdf", "docx"))
    date_uploaded = Column(DateTime)

    def __repr__(self):
        return "<Resume(%s : %s : %s>" % (self.id, self.filename, self.date_uploaded)


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True)
    you = Column(ForeignKey(User))


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
