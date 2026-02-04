# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

Base = declarative_base()

# 1. Try to read DATABASE_URL from env (Render / prod)
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle old-style Postgres URLs
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Local fallback (SQLite inside Motivator folder)
if not DATABASE_URL:
    fallback_path = os.path.join(os.path.dirname(__file__), "motivator.db")
    DATABASE_URL = f"sqlite:///{fallback_path}"
    print(f"[DB] No DATABASE_URL set. Using local fallback: {DATABASE_URL}")

elif DATABASE_URL.endswith("motivator.db") and not os.path.exists("motivator.db"):
    # In case DATABASE_URL points to a missing file (common dev bug)
    fallback_path = os.path.join(os.path.dirname(__file__), "motivator.db")
    DATABASE_URL = f"sqlite:///{fallback_path}"
    print(f"[DB] Local motivator.db not found. Using fallback path: {fallback_path}")

# 3. Create engine + session
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("DB URL:", engine.url)

# 4. Import models after Base (SQLAlchemy discovery)
from Motivator import models  # noqa: E402
