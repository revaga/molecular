from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres/db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MolecularTarget(Base):
    __tablename__ = "molecular_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    my = Column(Float)  # Membership degree
    mn = Column(Float)  # Non-membership degree
    hesitancy = Column(Float)  # Hesitancy degree
    confidence = Column(Float)  # Model confidence score
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "my": self.my,
            "mn": self.mn,
            "hesitancy": self.hesitancy,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }

class Therapy(Base):
    __tablename__ = "therapies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    my = Column(Float)  # Membership degree
    mn = Column(Float)  # Non-membership degree
    hesitancy = Column(Float)  # Hesitancy degree
    confidence = Column(Float)  # Model confidence score
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "my": self.my,
            "mn": self.mn,
            "hesitancy": self.hesitancy,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }

# Create tables
Base.metadata.create_all(bind=engine)
