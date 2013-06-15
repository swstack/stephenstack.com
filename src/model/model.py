from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative.api import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    def __init__(self, name, fullname, password=""):
        self.name = name
        self.fullname = fullname
        self.password = password

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.name, self.fullname, self.password)


if __name__ == "__main__":
    engine = create_engine('sqlite:///tutorial.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    user = User('Stephen', 'Stack')
    session.add(user)
    session.commit()
