# routes/admin.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from bson import ObjectId
from bson.errors import InvalidId

from db import users_col, predictions_col, chats_col
from core.templates import templates
from core.security import get_current_user, require_admin
from services.patient_service import to_utc_aware

router = APIRouter(tags=["admin"])

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    admin_user = users_col.find_one({"_id": ObjectId(user_id)})
    if not admin_user or admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    total_users = users_col.count_documents({})
    total_predictions = predictions_col.count_documents({})

    distinct_patient_ids = predictions_col.distinct("patient.patient_id")
    total_patients = len(distinct_patient_ids)

    today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_naive = today_utc.replace(tzinfo=None)

    today_filter = {
        "$or": [
            {"created_at": {"$gte": today_utc}},
            {"created_at": {"$gte": today_naive}},
        ]
    }
    today_predictions = predictions_col.count_documents(today_filter)

    pipeline_user_stats = [
        {"$match": {"user_id": {"$ne": None}}},
        {
            "$group": {
                "_id": "$user_id",
                "predictions_count": {"$sum": 1},
                "patients": {"$addToSet": "$patient.patient_id"},
                "last_activity": {"$max": "$created_at"},
            }
        },
    ]

    stats_by_user: dict = {}
    for row in predictions_col.aggregate(pipeline_user_stats):
        uid = row.get("_id")
        if not uid:
            continue
        stats_by_user[uid] = {
            "predictions_count": row.get("predictions_count", 0),
            "patients": row.get("patients", []),
            "last_activity": row.get("last_activity"),
        }

    users_for_template = []
    for u in users_col.find({}):
        uid = u["_id"]
        s = stats_by_user.get(uid, {})
        patients_count = len(s.get("patients", []))
        predictions_count = s.get("predictions_count", 0)

        last_activity = to_utc_aware(s.get("last_activity"))

        users_for_template.append(
            {
                "id": str(uid),
                "full_name": u.get("full_name") or "",
                "email": u.get("email") or "",
                "role": u.get("role", "user"),
                "patients_count": patients_count,
                "predictions_count": predictions_count,
                "last_activity": last_activity,
            }
        )

    users_for_template.sort(
        key=lambda x: x["last_activity"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "full_name": admin_user.get("full_name"),
            "user_email": admin_user.get("email"),
            "total_users": total_users,
            "total_patients": total_patients,
            "total_predictions": total_predictions,
            "today_predictions": today_predictions,
            "users": users_for_template,
        },
    )

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    admin_user = require_admin(request)

    pipeline = [
        {"$match": {"user_id": {"$ne": None}}},
        {
            "$group": {
                "_id": "$user_id",
                "predictions_count": {"$sum": 1},
                "patients": {"$addToSet": "$patient.patient_id"},
                "last_activity": {"$max": "$created_at"},
                "first_activity": {"$min": "$created_at"},
            }
        },
    ]

    stats_by_user = {row["_id"]: row for row in predictions_col.aggregate(pipeline)}
    now_utc = datetime.now(timezone.utc)

    users_for_template = []
    for u in users_col.find({}):
        uid = u["_id"]
        s = stats_by_user.get(uid, {})

        created_at = to_utc_aware(u.get("created_at"))
        first_activity = to_utc_aware(s.get("first_activity"))
        last_activity = to_utc_aware(s.get("last_activity"))

        start_date = created_at or first_activity
        days_using = (now_utc - start_date).days if start_date else 0
        patients_list = s.get("patients", []) or []

        users_for_template.append({
            "id": str(uid),
            "full_name": u.get("full_name") or "",
            "email": u.get("email") or "",
            "phone": u.get("phone") or "",
            "role": u.get("role", "user"),
            "status": u.get("status", "active"),
            "days_using": days_using,
            "patients_count": len(patients_list),
            "predictions_count": s.get("predictions_count", 0),
            "last_activity": last_activity,
        })

    users_for_template.sort(
        key=lambda x: x["last_activity"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "full_name": admin_user.get("full_name"),
            "user_email": admin_user.get("email"),
            "users": users_for_template,
        },
    )

@router.get("/admin/users/{user_id}")
async def admin_user_details(request: Request, user_id: str):
    require_admin(request)
    return RedirectResponse(url="/admin/users", status_code=302)

@router.post("/admin/users/{user_id}/toggle")
async def admin_toggle_user(request: Request, user_id: str):
    admin_user = require_admin(request)

    try:
        target_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    if str(admin_user["_id"]) == str(target_id):
        raise HTTPException(status_code=400, detail="You cannot disable your own account")

    u = users_col.find_one({"_id": target_id})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = "disabled" if u.get("status", "active") == "active" else "active"
    users_col.update_one(
        {"_id": target_id},
        {"$set": {"status": new_status}}
    )

    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/admin/users/{user_id}/toggle-role")
async def admin_toggle_user_role(request: Request, user_id: str):
    admin_user = require_admin(request)

    try:
        target_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    if str(admin_user["_id"]) == str(target_id):
        raise HTTPException(status_code=400, detail="You cannot alter your own admin role")

    u = users_col.find_one({"_id": target_id})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    new_role = "user" if u.get("role") == "admin" else "admin"
    users_col.update_one(
        {"_id": target_id},
        {"$set": {"role": new_role}}
    )

    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/admin/users/{user_id}/delete")
async def admin_delete_user(request: Request, user_id: str):
    admin_user = require_admin(request)

    try:
        target_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    if str(admin_user["_id"]) == str(target_id):
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    users_col.delete_one({"_id": target_id})
    predictions_col.delete_many({"user_id": target_id})
    chats_col.delete_many({"user_id": target_id})

    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/admin/users/{user_id}/edit")
async def admin_edit_user(
    request: Request,
    user_id: str,
    full_name: str = Form(""),
    phone: str = Form(""),
    role: str = Form("user"),
):
    admin_user = require_admin(request)

    try:
        target_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    if str(admin_user["_id"]) == str(target_id) and role != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role")

    role = "admin" if role == "admin" else "user"

    users_col.update_one(
        {"_id": target_id},
        {"$set": {"full_name": full_name.strip(), "phone": (phone or "").strip(), "role": role}},
    )
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/admin/patients", response_class=HTMLResponse)
async def admin_patients_page(request: Request):
    admin_user = require_admin(request)

    pipeline = [
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": "$patient.patient_id",
                "name": {"$first": "$patient.name"},
                "age": {"$first": "$patient.age"},
                "gender": {"$first": "$patient.gender"},
                "phone": {"$first": "$patient.phone"},
                "user_id": {"$first": "$user_id"},
                "last_label": {"$first": "$label"},
                "created_at": {"$first": "$created_at"},
            }
        },
        {"$sort": {"created_at": -1}},
    ]
    user_map = {str(u["_id"]): u.get("email", "Unknown") for u in users_col.find({}, {"email": 1})}

    patients = []
    for r in predictions_col.aggregate(pipeline):
        uid_str = str(r.get("user_id")) if r.get("user_id") else ""
        patients.append({
            "patient_id": r.get("_id"),
            "name": r.get("name", "Unnamed"),
            "age": r.get("age"),
            "gender": r.get("gender", "-"),
            "phone": r.get("phone", "-"),
            "user_email": user_map.get(uid_str, "N/A"),
            "last_label": r.get("last_label"),
            "created_at": to_utc_aware(r.get("created_at")),
        })

    return templates.TemplateResponse(
        "admin_patients.html",
        {
            "request": request,
            "full_name": admin_user.get("full_name"),
            "user_email": admin_user.get("email"),
            "patients": patients,
        },
    )

@router.get("/admin/predictions", response_class=HTMLResponse)
async def admin_predictions_page(request: Request):
    admin_user = require_admin(request)

    user_map = {str(u["_id"]): u.get("email", "Unknown") for u in users_col.find({}, {"email": 1})}

    predictions = []
    for doc in predictions_col.find({}).sort("created_at", -1).limit(250):
        pat = doc.get("patient", {}) or {}
        uid_str = str(doc.get("user_id")) if doc.get("user_id") else ""
        predictions.append({
            "patient_name": pat.get("name", "Unknown"),
            "patient_id": pat.get("patient_id", "-"),
            "inputs": doc.get("inputs"),
            "label": doc.get("label", "No prediction yet"),
            "user_email": user_map.get(uid_str, "Anonymous"),
            "created_at": to_utc_aware(doc.get("created_at")),
        })

    return templates.TemplateResponse(
        "admin_predictions.html",
        {
            "request": request,
            "full_name": admin_user.get("full_name"),
            "user_email": admin_user.get("email"),
            "predictions": predictions,
        },
    )

@router.get("/api/admin-charts")
async def admin_chart_data(request: Request):
    pipeline_latest = [
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": "$patient.patient_id",
                "label": {"$first": "$label"},
                "created_at": {"$first": "$created_at"},
            }
        },
    ]

    latest_docs = list(predictions_col.aggregate(pipeline_latest))

    counts_map: dict[str, int] = {}
    for doc in latest_docs:
        label = doc.get("label") or "Unknown"
        counts_map[label] = counts_map.get(label, 0) + 1

    label_counts = [
        {"label": label, "count": count} for label, count in counts_map.items()
    ]

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=29)

    day_labels: list[str] = []
    day_map: dict[str, dict[str, int]] = {}

    for i in range(30):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        day_labels.append(key)
        day_map[key] = {}

    for doc in latest_docs:
        created = doc.get("created_at")
        label = doc.get("label", "Unknown")
        if not created:
            continue

        created_aware = to_utc_aware(created)
        d = created_aware.date() if created_aware else None
        if not d or d < start_date or d > end_date:
            continue

        key = d.isoformat()
        bucket = day_map.get(key)
        if bucket is None:
            continue

        bucket[label] = bucket.get(label, 0) + 1

    alz_series = []
    no_alz_series = []

    for key in day_labels:
        bucket = day_map[key]
        alz_series.append(bucket.get("Alzheimer's Detected", 0))
        no_alz_series.append(bucket.get("No Alzheimer's", 0))

    data = {
        "label_counts": label_counts,
        "trend": {
            "dates": day_labels,
            "alzheimers": alz_series,
            "no_alzheimers": no_alz_series,
        },
    }

    return JSONResponse(data)
