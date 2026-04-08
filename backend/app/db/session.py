from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_and_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """
    Create a SQLAlchemy Engine and a configured sessionmaker bound to it.
    
    Parameters:
        database_url (str): Database URL used to create the Engine.
    
    Returns:
        tuple[Engine, sessionmaker[Session]]: The created Engine and a sessionmaker bound to that engine configured with autoflush=False, autocommit=False, and future=True.
    """
    engine = create_engine(database_url, future=True)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """
    Provide a database session to the caller and ensure it is closed after use.
    
    Parameters:
        session_factory (sessionmaker[Session]): Factory that produces SQLAlchemy Session instances.
    
    Returns:
        db (Session): A SQLAlchemy session instance yielded to the caller; the session is closed when the generator finishes.
    """
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
