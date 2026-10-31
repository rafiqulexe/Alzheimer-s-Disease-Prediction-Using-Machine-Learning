# core/security.py
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Request, HTTPException
from bson import ObjectId

from db import users_col
from core.config import JWT_SECRET, JWT_ALG

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_PASSWORD_BYTES = 72

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password too long for bcrypt")
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False

def create_token(user_id: str, role: str = "user") -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        return None

def get_current_user(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        return None, None
    data = decode_token(token)
    if not data:
        return None, None
    return data.get("sub"), data.get("role")

def require_admin(request: Request):
    user_id, role = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    u = users_col.find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=401, detail="User not found")
    return u
