from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.routers.appointments import serialize

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}/appointments")
def upcoming_appointments(patient_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Patient, patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    appts = (db.query(models.Appointment)
             .filter(models.Appointment.patient_id == patient_id,
                     models.Appointment.status == "booked",
                     models.Appointment.start_time >= datetime.now(timezone.utc))
             .order_by(models.Appointment.start_time)
             .all())
    return [serialize(a) for a in appts]