# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Dead: not used for any table metadata. All models attach to
# Motivator.models.Base instead (see models.py); that's the Base that
# app.py's /init-db and the test suite call create_all/drop_all against.
Base = declarative_base()

# 1. Try to read DATABASE_URL from env (Render / prod)
DATABASE_URL = os.getenv("DATABASE_URL")

# Handle old-style Postgres URLs
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Production is any environment running on Render, or Flask explicitly set to production.
IS_PRODUCTION = bool(os.getenv("RENDER")) or os.getenv("FLASK_ENV") == "production"

if IS_PRODUCTION:
    # Never fall back to SQLite in production — fail loudly instead of
    # silently writing/reading the wrong database.
    if not DATABASE_URL or not DATABASE_URL.startswith("postgresql"):
        raise RuntimeError(
            "DATABASE_URL is missing or is not a PostgreSQL URL in production "
            "(RENDER env var or FLASK_ENV=production detected). Refusing to "
            "fall back to SQLite."
        )
elif not DATABASE_URL:
    # 2. Local dev fallback (SQLite inside Motivator folder)
    fallback_path = os.path.join(os.path.dirname(__file__), "motivator.db")
    DATABASE_URL = f"sqlite:///{fallback_path}"
    print(f"[DB] No DATABASE_URL set. Using local fallback: {DATABASE_URL}")

# 3. Create engine + session
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Import models after Base (SQLAlchemy discovery)
from Motivator import models  # noqa: E402
