# routes/settings.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId

from db import users_col
from core.templates import templates
from core.security import (
    get_current_user,
    verify_password,
    hash_password,
)

router = APIRouter(tags=["settings"])

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user_id, role = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    u = users_col.find_one({"_id": ObjectId(user_id)})
    if not u:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "full_name": u.get("full_name", ""),
            "user_email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "role": role,
            "user_role": role,
        },
    )

@router.post("/settings/profile")
async def update_profile(
    request: Request,
    full_name: str = Form(""),
    phone: str = Form(""),
):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"full_name": full_name.strip(), "phone": phone.strip()}},
    )
    return RedirectResponse(url="/settings", status_code=302)

@router.post("/settings/password")
async def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    u = users_col.find_one({"_id": ObjectId(user_id)})
    if not u or not verify_password(current_password, u["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    hashed = hash_password(new_password)
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed}},
    )
    return RedirectResponse(url="/settings", status_code=302)
