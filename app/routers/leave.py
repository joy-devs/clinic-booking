from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.routers.doctors import serialize_leave
from app.services.booking import EAT

router = APIRouter(prefix="/leave", tags=["leave"])


@router.get("")
def clinic_leave(day: Optional[date] = Query(
                     None, alias="date",
                     description=("Optional. Leave empty to see every doctor's upcoming leave, "
                                  "or enter one date (YYYY-MM-DD) to see who is on leave that day.")),
                 db: Session = Depends(get_db)):
    """Who is on leave. Without a date: all doctors' upcoming leave. With a date: only the doctors off that day."""
    query = (db.query(models.DoctorLeave, models.Doctor.name)
             .join(models.Doctor, models.Doctor.id == models.DoctorLeave.doctor_id))
    if day:
        query = query.filter(models.DoctorLeave.start_date <= day,
                             models.DoctorLeave.end_date >= day)
    else:
        today = datetime.now(EAT).date()
        query = query.filter(models.DoctorLeave.end_date >= today)
    rows = query.order_by(models.DoctorLeave.start_date,
                          models.DoctorLeave.doctor_id).all()
    return [serialize_leave(leave, name) for leave, name in rows]