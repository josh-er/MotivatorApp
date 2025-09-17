from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    time = Column(String, nullable=False)  # format "HH:MM"
    last_sent = Column(Date, nullable=True)  # Track last send date
    cycle = Column(Integer, default=1, nullable=False)  # Track "quote cycles"

    sent_quotes = relationship("SentQuote", back_populates="user")


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)

    sent_quotes = relationship("SentQuote", back_populates="quote")


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False)
    quote = Column(String, nullable=False)
    status = Column(String, default="success")
    error = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SentQuote(Base):
    __tablename__ = "sent_quotes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    sent_date = Column(DateTime, default=datetime.utcnow)
    cycle = Column(Integer, nullable=False)  # Which cycle this quote was sent in

    user = relationship("User", back_populates="sent_quotes")
    quote = relationship("Quote", back_populates="sent_quotes")

    __table_args__ = (
        UniqueConstraint("user_id", "quote_id", "cycle", name="_user_quote_cycle_uc"),
    )
