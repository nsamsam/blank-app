import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    """Resolve the database URL from environment or Streamlit secrets."""
    url = os.getenv("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            pass
    if not url:
        raise RuntimeError(
            "DATABASE_URL not set. Add it to .env or .streamlit/secrets.toml"
        )
    return url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Yield a database session, closing it when done."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
