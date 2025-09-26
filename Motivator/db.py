# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # path to Motivator/
DB_PATH = os.path.join(BASE_DIR, "motivator.db")

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# relative import so package execution works
from Motivator.models import User, Quote  # noqa: E402
