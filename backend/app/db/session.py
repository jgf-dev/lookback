from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


engine = create_engine(get_settings().database_url, echo=False)


def init_db() -> None:
    """
    Initialize the database by creating all tables defined in SQLModel metadata on the configured engine.
    
    Creates any missing tables for models registered with `SQLModel.metadata`; existing tables are not modified.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Provide a SQLModel `Session` scoped to a context for use by callers (e.g., dependency injection).
    
    Returns:
        session (Session): An active `Session` bound to the module `engine`. The session is yielded for use and will be closed automatically when the context exits.
    """
    with Session(engine) as session:
        yield session