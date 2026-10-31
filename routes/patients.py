# routes/patients.py
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from bson import ObjectId

from db import users_col, predictions_col
from core.templates import templates
from core.security import get_current_user
from services.patient_service import (
    calculate_age_from_birthdate,
    get_or_create_patient_id,
)

router = APIRouter(tags=["patients"])

@router.get("/patients", response_class=HTMLResponse)
async def patients_page(request: Request):
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
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": "$patient.patient_id",
                "name": {"$first": "$patient.name"},
                "age": {"$first": "$patient.age"},
                "gender": {"$first": "$patient.gender"},
                "phone": {"$first": "$patient.phone"},
                "last_label": {"$first": "$label"},
                "created_at": {"$first": "$created_at"},
            }
        },
        {"$sort": {"created_at": -1}},
    ]

    patients = []
    for row in predictions_col.aggregate(pipeline):
        patients.append(
            {
                "patient_id": row["_id"],
                "name": row.get("name"),
                "age": row.get("age"),
                "gender": row.get("gender"),
                "phone": row.get("phone"),
                "last_label": row.get("last_label"),
                "created_at": row.get("created_at"),
            }
        )

    return templates.TemplateResponse(
        "patients.html",
        {
            "request": request,
            "user_email": user_email,
            "full_name": full_name,
            "patients": patients,
            "role": role,
            "user_role": role,
        },
    )

@router.post("/patients/manual")
async def add_patient_manual(
    request: Request,
    patient_name: str = Form(...),
    birthdate: str = Form(...),
    gender: str = Form(...),
    phone: str = Form(...)
):
    user_id, _ = get_current_user(request)
    if not user_id:
        return JSONResponse({"ok": False, "error": "not_logged_in"}, status_code=401)

    age = calculate_age_from_birthdate(birthdate)
    patient_id = get_or_create_patient_id(user_id, patient_name, birthdate, gender)

    patient_doc = {
        "name": patient_name.strip(),
        "patient_id": patient_id,
        "birthdate": birthdate,
        "age": age,
        "gender": gender,
        "phone": phone.strip(),
    }

    doc = {
        "user_id": ObjectId(user_id),
        "patient": patient_doc,
        "inputs": None,
        "prediction_index": None,
        "predicted_class": None,
        "label": "No prediction yet",
        "created_at": datetime.now(timezone.utc),
    }
    predictions_col.insert_one(doc)

    return JSONResponse({"ok": True, "patient_id": patient_id})

@router.get("/add-patient", response_class=HTMLResponse)
async def add_patient_page(request: Request):
    user_id, role = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user_email = None
    full_name = None
    u = users_col.find_one({"_id": ObjectId(user_id)})
    if u:
        user_email = u.get("email")
        full_name = u.get("full_name")

    return templates.TemplateResponse(
        "add_patient.html",
        {
            "request": request,
            "user_email": user_email,
            "full_name": full_name,
            "role": role,
            "user_role": role,
        }
    )

@router.get("/patients/{patient_id}/edit", response_class=HTMLResponse)
async def edit_patient_get(request: Request, patient_id: str):
    user_id, role = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    doc = predictions_col.find_one(
        {"user_id": ObjectId(user_id), "patient.patient_id": patient_id},
        sort=[("created_at", -1)],
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = doc.get("patient", {}) or {}

    user_email = None
    full_name = None
    u = users_col.find_one({"_id": ObjectId(user_id)})
    if u:
        user_email = u.get("email")
        full_name = u.get("full_name")

    return templates.TemplateResponse(
        "edit_patient.html",
        {
            "request": request,
            "user_id": user_id,
            "user_email": user_email,
            "full_name": full_name,
            "role": role,
            "user_role": role,
            "patient": patient,
        },
    )

@router.post("/patients/{patient_id}/edit", response_class=HTMLResponse)
async def edit_patient_post(
    request: Request,
    patient_id: str,
    name: str = Form(...),
    age: float = Form(None),
    gender: str = Form(...),
    phone: str = Form(None),
):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    update_fields: Dict[str, Any] = {
        "patient.name": name.strip(),
        "patient.gender": gender,
    }
    if age is not None:
        update_fields["patient.age"] = age
    if phone is not None:
        update_fields["patient.phone"] = phone.strip()

    predictions_col.update_many(
        {"user_id": ObjectId(user_id), "patient.patient_id": patient_id},
        {"$set": update_fields},
    )

    return RedirectResponse(url="/patients", status_code=302)

@router.post("/patients/{patient_id}/delete")
async def delete_patient(request: Request, patient_id: str):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    predictions_col.delete_many(
        {"user_id": ObjectId(user_id), "patient.patient_id": patient_id}
    )

    return RedirectResponse(url="/patients", status_code=302)
