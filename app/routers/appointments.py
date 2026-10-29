from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
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
    doctor: Optional[int] = None,
    patient: Optional[int] = None,
    date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    List appointments with optional query parameter filters:
    - `?doctor=1`
    - `?patient=4`
    - `?date=2026-10-29`
    - Or any combination of them.
    """
    appointments = get_filtered_appointments(
        db=db,
        doctor_id=doctor,
        patient_id=patient,
        appointment_date=date
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