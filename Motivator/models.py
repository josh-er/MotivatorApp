# Motivator/models.py
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=False)
    time = Column(String, nullable=False)         # HH:MM preferred send time
    last_sent = Column(Date, nullable=True)       # Track last date message was sent
