# db.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Load .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "alzheimers_app")

_client = None
_db = None

def get_db():
    """Lazily initialize and return the MongoDB database connection."""
    global _client, _db
    if _db is not None:
        return _db

    if not MONGODB_URI:
        raise ValueError("MONGODB_URI is not set in your .env file.")

    try:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        _db = _client[DB_NAME]
        return _db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB ({MONGODB_URI}): {e}")
        raise

class LazyCollection:
    """
    Proxy collection wrapper to avoid blocking SRV DNS resolution
    or crashing server startup when offline or database is starting.
    """
    def __init__(self, name: str):
        self._name = name

    def _get_collection(self):
        database = get_db()
        return database[self._name]

    def __getattr__(self, item):
        col = self._get_collection()
        return getattr(col, item)

    def __getitem__(self, item):
        col = self._get_collection()
        return col[item]

# Exported Collections (lazily resolved)
users_col = LazyCollection("users")
predictions_col = LazyCollection("predictions")
chats_col = LazyCollection("chats")
