# routes/reports.py
import csv
import io
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId

from db import users_col, predictions_col
from core.templates import templates
from core.security import get_current_user

router = APIRouter(tags=["reports"])

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
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
    total_preds = predictions_col.count_documents({"user_id": ObjectId(user_id)})

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "user_email": user_email,
            "full_name": full_name,
            "predictions_count": total_preds,
            "patients_count": unique_patients,
            "role": role,
            "user_role": role,
        },
    )

@router.get("/reports/predictions.csv")
async def export_predictions_csv(request: Request):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    cursor = predictions_col.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Patient ID", "Patient Name", "Age", "Gender", "Phone",
        "Memory Complaints", "Behavioral Problems", "ADL", "MMSE", "Functional Assessment",
        "Predicted Class", "Diagnosis Label", "Created At"
    ])
    for doc in cursor:
        pat = doc.get("patient", {}) or {}
        inp = doc.get("inputs", {}) or {}
        writer.writerow([
            pat.get("patient_id", ""),
            pat.get("name", ""),
            pat.get("age", ""),
            pat.get("gender", ""),
            pat.get("phone", ""),
            inp.get("memory_complaints", "") if inp else "",
            inp.get("behavioral_problems", "") if inp else "",
            inp.get("adl", "") if inp else "",
            inp.get("mmse", "") if inp else "",
            inp.get("functional_assessment", "") if inp else "",
            doc.get("predicted_class", ""),
            doc.get("label", ""),
            doc.get("created_at", ""),
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions_report.csv"}
    )

@router.get("/reports/patients.csv")
async def export_patients_csv(request: Request):
    user_id, _ = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

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
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Patient ID", "Name", "Age", "Gender", "Phone", "Latest Prediction", "Last Updated"])
    for p in predictions_col.aggregate(pipeline):
        writer.writerow([
            p.get("_id", ""),
            p.get("name", ""),
            p.get("age", ""),
            p.get("gender", ""),
            p.get("phone", ""),
            p.get("last_label", ""),
            p.get("created_at", ""),
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=patients_report.csv"}
    )
