from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from .config import settings

engine_options = {"pool_pre_ping": True}
# Supabase's pooler already manages connection pooling. Avoid a second persistent
# SQLAlchemy pool, which also works cleanly with transaction-mode poolers.
if "pooler.supabase.com" in settings.database_url:
    engine_options["poolclass"] = NullPool

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
