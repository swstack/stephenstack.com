from sqlalchemy import Column, Integer, String, Enum, DateTime, LargeBinary
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.schema import ForeignKey
from datetime import datetime
import json

Base = declarative_base()


def _strftime(dt):
    return datetime.strftime(dt, "%d/%m/%y %H:%M")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    gapi_id = Column(String)
    name = Column(String)
    thumbnail_url = Column(String)
    profile_pic_url = Column(String)

    def __init__(self, gapi_id, name, thumbnail_url, profile_pic_url):
        self.gapi_id = gapi_id
        self.name = name
        self.thumbnail_url = thumbnail_url
        self.profile_pic_url = profile_pic_url

    def __repr__(self):
        return "<User(%s : %s)>" % (self.id, self.name)

    def to_json(self, encode=False):
        obj = {
               "gapi_id": self.gapi_id,
               "name": self.name,
               "thumbnail": self.thumbnail_url,
              }
        if encode:
            return json.dumps(obj)
        else:
            return obj


class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer, primary_key=True)
    filedata = Column(LargeBinary)
    filename = Column(String)
    filetype = Column(Enum("pdf", "docx"))
    datetime_uploaded = Column(DateTime)

    def __init__(self, filedata, filename, filetype, date_uploaded):
        self.filedata = filedata
        self.filename = filename
        self.filetype = filetype
        self.date_uploaded = date_uploaded

    def __repr__(self):
        return "<Resume(%s : %s : %s>" % (self.id, self.filename, self.date_uploaded)


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    sender = Column(ForeignKey(User.id))
    receiver = Column(ForeignKey(User.id))
    msg_data = Column(String)
    datetime_sent = Column(DateTime)

    def __init__(self, sender, receiver, msg_data, datetime_sent):
        self.sender = sender
        self.receiver = receiver
        self.msg_data = msg_data
        self.datetime_sent = datetime_sent

    def __repr__(self):
        return "<Message(from %s to %s : %s>" % (self.sender,
                                                 self.receiver,
                                                 self.msg_data)

    def to_json(self, encode=False):
        obj = {
               "sender": self.sender,
               "receiver": self.receiver,
               "timestamp": _strftime(self.datetime_sent),
               "msg": self.msg_data,
              }
        if encode:
            return json.dumps(obj)
        else:
            return obj
