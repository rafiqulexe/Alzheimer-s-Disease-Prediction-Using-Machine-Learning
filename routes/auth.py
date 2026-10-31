# routes/auth.py
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from db import users_col
from core.templates import templates
from core.security import (
    hash_password,
    verify_password,
    create_token,
)
from core.config import is_admin_email

router = APIRouter(tags=["auth"])

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "message": ""},
    )

@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    age: int = Form(None),
    phone: str = Form(None),
):
    email_clean = email.strip().lower()

    existing = users_col.find_one({"email": email_clean})
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "message": "Email already registered."},
        )

    try:
        hashed = hash_password(password)
    except ValueError:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "message": "Password too long. Please use a password of 72 characters or less.",
            },
        )

    role = "admin" if is_admin_email(email_clean) else "user"
    now_utc = datetime.now(timezone.utc)

    user = {
        "full_name": full_name.strip(),
        "email": email_clean,
        "password": hashed,
        "age": age,
        "phone": (phone or "").strip(),
        "role": role,
        "status": "active",
        "created_at": now_utc,
    }

    result = users_col.insert_one(user)
    token = create_token(str(result.inserted_id), role=role)

    redirect_to = "/admin" if role == "admin" else "/dashboard"
    resp = RedirectResponse(url=redirect_to, status_code=302)
    resp.set_cookie("auth_token", token, httponly=True, max_age=60 * 60 * 12, samesite="lax")
    return resp

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "message": ""},
    )

@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    email_clean = email.strip().lower()

    user = users_col.find_one({"email": email_clean})
    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Invalid email or password."},
        )

    if user.get("status") == "disabled":
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Account is disabled. Please contact an administrator."},
        )

    role = "admin" if is_admin_email(email_clean) else user.get("role", "user")
    users_col.update_one({"_id": user["_id"]}, {"$set": {"role": role}})

    token = create_token(str(user["_id"]), role=role)

    redirect_to = "/admin" if role == "admin" else "/dashboard"
    resp = RedirectResponse(url=redirect_to, status_code=302)
    resp.set_cookie("auth_token", token, httponly=True, max_age=60 * 60 * 12, samesite="lax")
    return resp

@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("auth_token")
    return resp

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_get(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request},
    )

@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_post(request: Request, email: str = Form(...)):
    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request,
            "message": "If an account with that email exists, password reset instructions have been dispatched.",
        },
    )
