from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.booking import get_available_slots, SLOT, EAT

router = APIRouter(prefix="/doctors", tags=["doctors"])


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
            {"start": s.astimezone(EAT).isoformat(),
             "end": (s + SLOT).astimezone(EAT).isoformat()}
            for s in slots
        ],
    }