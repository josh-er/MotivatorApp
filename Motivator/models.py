from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)

    # New fields:
    # local_time = the time user chose in their local timezone (HH:MM)
    # timezone = IANA timezone string (e.g. "America/Los_Angeles")
    # utc_time = the normalized UTC HH:MM equivalent stored for scheduling comparison
    local_time = Column(String, nullable=True)   # "HH:MM" as user-submitted local time
    timezone = Column(String, nullable=True)     # IANA timezone like "America/New_York"
    utc_time = Column(String, nullable=True)     # normalized HH:MM in UTC

    # legacy `time` kept for compatibility during migration (optional)
    time = Column(String, nullable=True)  # old field — will be kept for now

    last_sent = Column(Date, nullable=True)
    cycle = Column(Integer, default=1, nullable=False)
    last_quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)

    opted_in = Column(Boolean, default=True)
    received_compliance = Column(Boolean, default=False)

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
    quote = Column(String, nullable=True)
    status = Column(String, default="success")
    error = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SentQuote(Base):
    __tablename__ = "sent_quotes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    sent_date = Column(DateTime, default=datetime.utcnow)
    cycle = Column(Integer, nullable=False)

    user = relationship("User", back_populates="sent_quotes")
    quote = relationship("Quote", back_populates="sent_quotes")

    __table_args__ = (
        UniqueConstraint("user_id", "quote_id", "cycle", name="_user_quote_cycle_uc"),
    )