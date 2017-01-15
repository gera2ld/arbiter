from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from social_tornado.models import init_social
from . import settings

__all__ = [
    'session', 'User',
]

def init():
    Base.metadata.create_all(engine)

engine = create_engine(
    settings.DB_ENGINE or 'sqlite:///:memory:',
    echo=settings.PYTHON_ENV != 'production')
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

def json_transformer(default_fields):
    def as_json(model, extra_fields=()):
        result = {}
        for fields in default_fields, extra_fields:
            for field in fields:
                result[field] = getattr(model, field)
        return result
    return as_json

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(64))
    email = Column(String(64))

    def __str__(self):
        return '<User %s>' % self.username

init_social(Base, session, settings.as_dict())

if not settings.DB_ENGINE:
    init()
