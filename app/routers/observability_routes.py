
from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Doctor, Patient, Appointment
from app.auth import verify_api_key

router = APIRouter(prefix="/insights", tags=["observability"])

@router.get("/summary", dependencies=[Security(verify_api_key)])
def get_app_insights_summary(db: Session = Depends(get_db)):
    """
    Returns high-level application metrics for real-time monitoring and dashboards.
    """
    total_doctors = db.query(Doctor).count()
    total_patients = db.query(Patient).count()
    total_appointments = db.query(Appointment).count()
    
    return {
        "status": "healthy",
        "database": "connected",
        "counts": {
            "doctors": total_doctors,
            "patients": total_patients,
            "appointments": total_appointments
        },
        "observability": {
            "metrics_endpoint": "/metrics",
            "logging": "structured_json"
        }
    }