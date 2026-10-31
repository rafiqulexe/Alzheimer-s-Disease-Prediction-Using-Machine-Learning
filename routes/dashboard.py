# routes/dashboard.py
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from bson import ObjectId

from db import users_col, predictions_col
from core.templates import templates
from core.security import get_current_user
from services.patient_service import to_utc_aware

router = APIRouter(tags=["dashboard"])

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user_id, _ = get_current_user(request)
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user_id, role = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user_email = None
    full_name = None

    u = users_col.find_one({"_id": ObjectId(user_id)})
    if u:
        user_email = u.get("email")
        full_name = u.get("full_name")

    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {"_id": "$patient.patient_id"}}
    ]
    unique_patients = len(list(predictions_col.aggregate(pipeline)))
    total_predictions = predictions_col.count_documents({"user_id": ObjectId(user_id)})

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user_email": user_email,
            "full_name": full_name,
            "predictions_count": total_predictions,
            "patients_count": unique_patients,
            "role": role,
            "user_role": role,
        },
    )

@router.get("/api/dashboard-charts")
async def dashboard_chart_data(request: Request):
    """
    Returns aggregated data for dashboard charts based on UNIQUE PATIENTS:
    - label_counts: how many patients in each label (using their latest prediction)
    - trend: daily patient counts for last 14 days for each label
    """
    user_id, _ = get_current_user(request)

    match_filter: Dict[str, Any] = {}
    if user_id:
        match_filter["user_id"] = ObjectId(user_id)

    pipeline_latest = []
    if match_filter:
        pipeline_latest.append({"$match": match_filter})

    pipeline_latest.extend(
        [
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$patient.patient_id",
                    "label": {"$first": "$label"},
                    "created_at": {"$first": "$created_at"},
                }
            },
        ]
    )

    latest_docs = list(predictions_col.aggregate(pipeline_latest))

    def canonical_label(raw: str) -> str:
        if raw is None:
            return "No prediction yet"
        s = str(raw).strip()
        if s in ["1", "Alzheimer", "Alzheimer's Disease", "AD", "Alzheimer's Detected"]:
            return "Alzheimer's Detected"
        if "No Alzheimer" in s:
            return "No Alzheimer's"
        return "No prediction yet"

    buckets = {
        "Alzheimer's Detected": 0,
        "No Alzheimer's": 0,
        "No prediction yet": 0,
    }

    for doc in latest_docs:
        raw_label = doc.get("label")
        canon = canonical_label(raw_label)
        buckets[canon] = buckets.get(canon, 0) + 1

    label_counts = [
        {"label": "Alzheimer's Detected", "count": buckets["Alzheimer's Detected"]},
        {"label": "No Alzheimer's", "count": buckets["No Alzheimer's"]},
        {"label": "No prediction yet", "count": buckets["No prediction yet"]},
    ]

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=13)

    day_labels: list[str] = []
    day_map: Dict[str, Dict[str, int]] = {}
    for i in range(14):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        day_labels.append(key)
        day_map[key] = {
            "Alzheimer's Detected": 0,
            "No Alzheimer's": 0,
        }

    for doc in latest_docs:
        created = doc.get("created_at")
        raw_label = doc.get("label")
        if not created:
            continue

        created_aware = to_utc_aware(created)
        d = created_aware.date() if created_aware else None
        if not d or d < start_date or d > end_date:
            continue

        key = d.isoformat()
        if key not in day_map:
            continue

        canon = canonical_label(raw_label)
        if canon in ("Alzheimer's Detected", "No Alzheimer's"):
            day_map[key][canon] += 1

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
