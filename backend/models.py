from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

DATABASE_URL = "postgresql://user:password@postgres/db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MolecularTarget(Base):
    __tablename__ = "molecular_targets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    my = Column(Float)
    mn = Column(Float)
    hesitancy = Column(Float)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Therapy(Base):
    __tablename__ = "therapies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    my = Column(Float)
    mn = Column(Float)
    hesitancy = Column(Float)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
