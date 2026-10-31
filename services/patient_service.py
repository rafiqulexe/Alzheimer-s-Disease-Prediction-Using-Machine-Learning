# services/patient_service.py
from datetime import datetime, date, timezone
from bson import ObjectId
from db import predictions_col

def calculate_age_from_birthdate(birthdate_str: str):
    """
    birthdate_str: 'YYYY-MM-DD'
    returns age in whole years (int) or None if invalid
    """
    try:
        dob = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

    today = date.today()
    age = today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )
    return age

def get_or_create_patient_id(
    user_id: str | None,
    name: str,
    birthdate_str: str,
    gender: str,
):
    """
    If a patient with same name + birthdate + gender for this user exists,
    reuse their patient_id. Otherwise generate a new one based on birthdate.
    """
    user_obj_id = ObjectId(user_id) if user_id else None

    query = {
        "user_id": user_obj_id,
        "patient.name": name,
        "patient.birthdate": birthdate_str,
        "patient.gender": gender,
    }
    existing = predictions_col.find_one(query)
    if existing:
        patient = existing.get("patient", {}) or {}
        existing_id = patient.get("patient_id")
        if existing_id:
            return existing_id

    # No existing patient -> generate new ID: YYYYMMDD-serial
    base = birthdate_str.replace("-", "") if birthdate_str else "00000000"
    count_same_dob = predictions_col.count_documents(
        {
            "user_id": user_obj_id,
            "patient.birthdate": birthdate_str,
        }
    )
    serial = count_same_dob + 1
    return f"{base}-{serial}"

def to_utc_aware(dt):
    """Convert Mongo datetime to UTC-aware datetime so comparisons never crash."""
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
