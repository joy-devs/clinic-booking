from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import DoctorCreate, WorkingHoursIn
from app.services.booking import (get_available_slots, get_day_slots,
                                  make_slot_id, SLOT, EAT)

router = APIRouter(prefix="/doctors", tags=["doctors"])


def serialize_doctor(d):
    return {
        "id": d.id,
        "name": d.name,
        "specialty": d.specialty,
        "working_hours": [
            {"weekday": h.weekday,
             "start_time": h.start_time.isoformat(),
             "end_time": h.end_time.isoformat()}
            for h in sorted(d.working_hours, key=lambda x: x.weekday)
        ],
    }


def check_hours(h: WorkingHoursIn):
    if h.end_time <= h.start_time:
        raise HTTPException(status_code=422,
                            detail="end_time must be after start_time.")
    for t in (h.start_time, h.end_time):
        if t.minute % 30 != 0 or t.second or t.microsecond:
            raise HTTPException(status_code=422,
                                detail="Times must be on the hour or half hour.")


@router.get("")
def list_doctors(db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).order_by(models.Doctor.id).all()
    return [serialize_doctor(d) for d in doctors]


@router.post("", status_code=201)
def create_doctor(body: DoctorCreate, db: Session = Depends(get_db)):
    for h in body.working_hours:
        check_hours(h)
    doctor = models.Doctor(name=body.name, specialty=body.specialty)
    db.add(doctor)
    db.flush()
    for h in body.working_hours:
        db.add(models.WorkingHours(doctor_id=doctor.id, weekday=h.weekday,
                                   start_time=h.start_time, end_time=h.end_time))
    db.commit()
    db.refresh(doctor)
    return serialize_doctor(doctor)


@router.post("/{doctor_id}/working-hours")
def set_working_hours(doctor_id: int, body: WorkingHoursIn,
                      db: Session = Depends(get_db)):
    doctor = db.get(models.Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    check_hours(body)
    # Replaces any existing hours for that weekday so ranges never overlap
    db.query(models.WorkingHours).filter_by(
        doctor_id=doctor_id, weekday=body.weekday).delete()
    db.add(models.WorkingHours(doctor_id=doctor_id, weekday=body.weekday,
                               start_time=body.start_time, end_time=body.end_time))
    db.commit()
    db.refresh(doctor)
    return serialize_doctor(doctor)


@router.get("/{doctor_id}/working-hours")
def get_working_hours(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(models.Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return serialize_doctor(doctor)


@router.get("/{doctor_id}/availability")
def availability(doctor_id: int,
                 day: date = Query(..., alias="date"),
                 db: Session = Depends(get_db)):
    if not db.get(models.Doctor, doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    slots = get_available_slots(db, doctor_id, day)
    return {
        "doctor_id": doctor_id,
        "date": day.isoformat(),
        "slots": [
            {"slot_id": make_slot_id(doctor_id, s),
             "start": s.astimezone(EAT).isoformat(),
             "end": (s + SLOT).astimezone(EAT).isoformat()}
            for s in slots
        ],
    }


@router.get("/{doctor_id}/slots")
def day_slots(doctor_id: int,
              day: date = Query(..., alias="date"),
              db: Session = Depends(get_db)):
    if not db.get(models.Doctor, doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {
        "doctor_id": doctor_id,
        "date": day.isoformat(),
        "slots": [
            {"slot_id": make_slot_id(doctor_id, s),
             "start": s.astimezone(EAT).isoformat(),
             "end": (s + SLOT).astimezone(EAT).isoformat(),
             "status": status}
            for s, status in get_day_slots(db, doctor_id, day)
        ],
    }