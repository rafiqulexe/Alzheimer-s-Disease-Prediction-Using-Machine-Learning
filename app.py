# app.py
"""
Alzheimer's Disease Prediction & Clinical Assistant
Main Application Entrypoint
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import modular routers
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from routes.patients import router as patients_router
from routes.predictions import router as predictions_router
from routes.assistant import router as assistant_router
from routes.reports import router as reports_router
from routes.settings import router as settings_router
from routes.admin import router as admin_router

# Convenience re-exports for backwards-compatibility & unit tests
from db import users_col, predictions_col, chats_col
from core.security import verify_password, hash_password, create_token, get_current_user
from core.config import is_admin_email

# Initialize FastAPI Application
app = FastAPI(
    title="Alzheimer's Disease Detection & Clinical Assistant",
    description="A modular clinical decision-support and RAG assistant system for Alzheimer's disease.",
    version="2.0.0",
)

# Mount static files directory
static_path = Path(__file__).resolve().parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Register feature routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(patients_router)
app.include_router(predictions_router)
app.include_router(assistant_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(admin_router)
