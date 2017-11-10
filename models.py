from sqlalchemy import create_engine, Column, Integer, String, Boolean,\
                       Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database


Base = declarative_base()


def init_models(db_engine_url):
    if not database_exists(db_engine_url):
        create_database(db_engine_url)
    engine = create_engine(db_engine_url, pool_recycle=18000)

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    return session


class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(String(15), nullable=False, unique=True, index=True)
    username = Column(String(50))
    full_name = Column(String(50))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    chats = relationship('User_Chat', back_populates='user')

    # def __repr__(self):
    #    return "<User(name='%s', fullname='%s', password='%s')>" % (
    #                         self.name, self.fullname, self.password)


class Chat(Base):
    __tablename__ = 'Chats'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    chat_id = Column(String(15), nullable=False, unique=True, index=True)
    chat_type = Column(String(20), nullable=False)
    title = Column(String(50))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    users = relationship('User_Chat', back_populates='chat')


class User_Chat(Base):
    __tablename__ = 'User_Chat'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('Users.id'), index=True)
    chat_id = Column(Integer, ForeignKey('Chats.id'), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())

    user = relationship('User', back_populates='chats')
    chat = relationship('Chat', back_populates='users')
    messages = relationship('Message', back_populates='user_chat_s')


class Message(Base):
    __tablename__ = 'Messages'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_chat_id = Column(Integer, ForeignKey('User_Chat.id'), index=True)
    cinema_id = Column(Integer, ForeignKey('Cinemas.id'), index=True)
    content_type = Column(String(30), nullable=False)
    is_valid = Column(Boolean, nullable=False, server_default='0')
    replied = Column(Boolean, nullable=False, server_default='0')
    text = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user_chat_s = relationship('User_Chat', back_populates='messages')
    cinema = relationship('Cinema', back_populates='messages')
    error = relationship('Error', back_populates='message')


class Cinema(Base):
    __tablename__ = 'Cinemas'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    cid = Column(Integer, nullable=False, unique=True, index=True)
    title = Column(String(50), nullable=False)
    city = Column(String(40))
    address = Column(String(150))
    phone = Column(String(100))
    url = Column(String(150), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    messages = relationship('Message', back_populates='cinema')


class Error(Base):
    __tablename__ = 'Errors'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey('Messages.id'), index=True)
    type = Column(String(100))
    traceback = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    message = relationship('Message', back_populates='error')
