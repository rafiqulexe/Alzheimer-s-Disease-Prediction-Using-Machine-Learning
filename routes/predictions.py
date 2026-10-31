# routes/predictions.py
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from bson import ObjectId

from db import users_col, predictions_col
from core.templates import templates
from core.security import get_current_user
from services.patient_service import (
    calculate_age_from_birthdate,
    get_or_create_patient_id,
)
from services.ml_service import predict_alzheimers

router = APIRouter(tags=["predictions"])

@router.get("/prediction", response_class=HTMLResponse)
async def prediction_page(request: Request):
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
        "prediction.html",
        {
            "request": request,
            "user_id": user_id,
            "user_email": user_email,
            "full_name": full_name,
            "role": role,
            "user_role": role,
        },
    )

@router.post("/predict")
async def predict_api(
    request: Request,
    patient_name: str = Form(...),
    birthdate: str = Form(...),
    gender: str = Form(...),
    phone: str = Form(None),
    memory_complaints: float = Form(...),
    behavioral_problems: float = Form(...),
    adl: float = Form(...),
    mmse: float = Form(...),
    functional_assessment: float = Form(...),
):
    try:
        pred_idx, class_label, status = predict_alzheimers(
            memory_complaints=memory_complaints,
            behavioral_problems=behavioral_problems,
            adl=adl,
            mmse=mmse,
            functional_assessment=functional_assessment,
        )
    except Exception as e:
        return JSONResponse(
            {"error": f"Model inference error: {e}"},
            status_code=503
        )

    user_id, _ = get_current_user(request)
    age = calculate_age_from_birthdate(birthdate)
    patient_id = get_or_create_patient_id(user_id, patient_name, birthdate, gender)

    patient_doc = {
        "name": patient_name.strip(),
        "patient_id": patient_id,
        "birthdate": birthdate,
        "age": age,
        "gender": gender,
        "phone": (phone or "").strip(),
    }

    doc = {
        "user_id": ObjectId(user_id) if user_id else None,
        "patient": patient_doc,
        "inputs": {
            "memory_complaints": memory_complaints,
            "behavioral_problems": behavioral_problems,
            "adl": adl,
            "mmse": mmse,
            "functional_assessment": functional_assessment,
        },
        "prediction_index": pred_idx,
        "predicted_class": class_label,
        "label": status,
        "created_at": datetime.now(timezone.utc),
    }
    predictions_col.insert_one(doc)

    return JSONResponse(
        {
            "prediction_index": pred_idx,
            "predicted_class": class_label,
            "label": status,
            "patient_id": patient_id,
        }
    )
