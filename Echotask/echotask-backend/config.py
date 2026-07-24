import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")  # Loads values from .env file


def _database_uri():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return f"sqlite:///{(BASE_DIR / 'instance' / 'echotask.db').as_posix()}"

    if database_url.startswith("sqlite:///"):
        path_value = database_url.replace("sqlite:///", "", 1)
        db_path = Path(path_value)
        if not db_path.is_absolute():
            return f"sqlite:///{(BASE_DIR / db_path).resolve().as_posix()}"

    return database_url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
