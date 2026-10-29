from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AppointmentCreate, CancelRequest, RescheduleRequest
from app.services.booking import (book_appointment, cancel_appointment,
                                 reschedule_appointment, get_filtered_appointments,
                                 make_slot_id, parse_slot_id, BookingError, as_utc, EAT)

router = APIRouter(prefix="/appointments", tags=["appointments"])


def serialize(a):
    return {
        "appointment_id": a.id,
        "slot_id": make_slot_id(a.doctor_id, a.start_time),
        "doctor_id": a.doctor_id,
        "patient_id": a.patient_id,
        "start": as_utc(a.start_time).astimezone(EAT).isoformat(),
        "end": as_utc(a.end_time).astimezone(EAT).isoformat(),
        "status": a.status,
        "cancel_reason": a.cancel_reason,
    }


@router.get("")
def list_appointments(
    appointment_id: Optional[str] = None,
    doctor: Optional[str] = None,
    patient: Optional[str] = None,
    date: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List appointments. Leave filters blank to list all appointments, 
    or filter by:
    - `?appointment_id=1`
    - `?doctor=1`
    - `?patient=4`
    - `?date=2026-11-11`
    - `?start_time=2026-11-11T09:30:00+03:00`
    - `?end_time=2026-11-11T10:00:00+03:00`
    """
    appt_id = int(appointment_id) if appointment_id and appointment_id.strip() else None
    doc_id = int(doctor) if doctor and doctor.strip() else None
    pat_id = int(patient) if patient and patient.strip() else None
    
    parsed_date = None
    if date and date.strip():
        try:
            parsed_date = date.fromisoformat(date.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    parsed_start = None
    if start_time and start_time.strip():
        try:
            parsed_start = datetime.fromisoformat(start_time.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format (e.g. 2026-11-11T09:30:00+03:00).")

    parsed_end = None
    if end_time and end_time.strip():
        try:
            parsed_end = datetime.fromisoformat(end_time.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format (e.g. 2026-11-11T10:00:00+03:00).")

    appointments = get_filtered_appointments(
        db=db,
        doctor_id=doc_id,
        patient_id=pat_id,
        appointment_date=parsed_date,
        appointment_id=appt_id,
        start_time=parsed_start,
        end_time=parsed_end
    )
    return [serialize(a) for a in appointments]


@router.post("", status_code=201)
def create_appointment(body: AppointmentCreate, db: Session = Depends(get_db)):
    start = body.start_time
    if body.slot_id:
        slot_doctor, start = parse_slot_id(body.slot_id)
        if slot_doctor != body.doctor_id:
            raise BookingError(400, "slot_id belongs to a different doctor.")
    return serialize(book_appointment(db, body.doctor_id, body.patient_id, start))


@router.patch("/{appointment_id}/cancel")
def cancel(appointment_id: int, body: CancelRequest, db: Session = Depends(get_db)):
    return serialize(cancel_appointment(db, appointment_id, body.reason))


@router.patch("/{appointment_id}/reschedule")
def reschedule(appointment_id: int, body: RescheduleRequest, db: Session = Depends(get_db)):
    return serialize(reschedule_appointment(db, appointment_id, body.start_time))