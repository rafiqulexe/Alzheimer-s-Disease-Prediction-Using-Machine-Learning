# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_super_secret_production_key")
JWT_ALG = "HS256"

def get_admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}

def is_admin_email(email: str) -> bool:
    return email.strip().lower() in get_admin_emails()
