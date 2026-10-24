from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AppointmentCreate
from app.services.booking import book_appointment, as_utc, EAT

router = APIRouter(prefix="/appointments", tags=["appointments"])


def serialize(a):
    return {
        "id": a.id,
        "doctor_id": a.doctor_id,
        "patient_id": a.patient_id,
        "start": as_utc(a.start_time).astimezone(EAT).isoformat(),
        "end": as_utc(a.end_time).astimezone(EAT).isoformat(),
        "status": a.status,
        "cancel_reason": a.cancel_reason,
    }


@router.post("", status_code=201)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db)):
    appt = book_appointment(db, body.doctor_id, body.patient_id, body.start_time)
    return serialize(appt)