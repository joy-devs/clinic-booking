from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import PatientCreate
from app.routers.appointments import serialize

router = APIRouter(prefix="/patients", tags=["patients"])


def serialize_patient(p):
    return {"patient_id": p.id, "name": p.name, "phone": p.phone}


@router.get("")
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).order_by(models.Patient.id).all()
    return [serialize_patient(p) for p in patients]


@router.post("", status_code=201)
def create_patient(body: PatientCreate, db: Session = Depends(get_db)):
    patient = models.Patient(name=body.name, phone=body.phone)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return serialize_patient(patient)


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