from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    time = Column(String, nullable=False)  # format "HH:MM"
    last_sent = Column(Date, nullable=True)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False)
    quote = Column(String, nullable=False)
    status = Column(String, default="success")
    error = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
