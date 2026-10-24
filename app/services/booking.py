from datetime import datetime, date, time, timedelta, timezone
from app import models
from sqlalchemy.exc import IntegrityError

EAT = timezone(timedelta(hours=3))  # Nairobi, no daylight saving
SLOT = timedelta(minutes=30)


def as_utc(dt: datetime) -> datetime:
    # SQLite returns naive datetimes; we always store UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_available_slots(db, doctor_id: int, day: date):
    hours = (db.query(models.WorkingHours)
             .filter_by(doctor_id=doctor_id, weekday=day.weekday())
             .all())
    if not hours:
        return []

    day_start = datetime.combine(day, time.min, tzinfo=EAT).astimezone(timezone.utc)
    day_end = day_start + timedelta(days=1)

    booked = {
        as_utc(a.start_time)
        for a in db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor_id,
            models.Appointment.status == "booked",
            models.Appointment.start_time >= day_start,
            models.Appointment.start_time < day_end,
        )
    }

    now = datetime.now(timezone.utc)
    slots = []
    for h in hours:
        cur = datetime.combine(day, h.start_time, tzinfo=EAT)
        end = datetime.combine(day, h.end_time, tzinfo=EAT)
        while cur + SLOT <= end:
            start = cur.astimezone(timezone.utc)
            if start > now and start not in booked:
                slots.append(start)
            cur += SLOT
    return sorted(slots)

class BookingError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def to_utc(dt: datetime) -> datetime:
    # Input without a timezone is treated as Nairobi time
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
    return dt.astimezone(timezone.utc)


def validate_slot(db, doctor_id: int, start: datetime):
    local = start.astimezone(EAT)
    if local.minute % 30 != 0 or local.second or local.microsecond:
        raise BookingError(400, "Appointments must start on the hour or half hour.")
    if start <= datetime.now(timezone.utc):
        raise BookingError(400, "Cannot book a time in the past.")

    hours = (db.query(models.WorkingHours)
             .filter_by(doctor_id=doctor_id, weekday=local.weekday())
             .all())
    within = any(
        datetime.combine(local.date(), h.start_time, tzinfo=EAT) <= local
        and local + SLOT <= datetime.combine(local.date(), h.end_time, tzinfo=EAT)
        for h in hours
    )
    if not within:
        raise BookingError(400, "Slot is outside the doctor's working hours.")

    taken = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.start_time == start,
        models.Appointment.status == "booked",
    ).first()
    if taken:
        raise BookingError(409, "That slot is already booked.")


def book_appointment(db, doctor_id: int, patient_id: int, start: datetime):
    start = to_utc(start)
    if not db.get(models.Doctor, doctor_id):
        raise BookingError(404, "Doctor not found.")
    if not db.get(models.Patient, patient_id):
        raise BookingError(404, "Patient not found.")
    validate_slot(db, doctor_id, start)

    appt = models.Appointment(doctor_id=doctor_id, patient_id=patient_id,
                              start_time=start, end_time=start + SLOT,
                              status="booked")
    db.add(appt)
    try:
        db.commit()
    except IntegrityError:  # two requests at the same instant
        db.rollback()
        raise BookingError(409, "That slot was just booked by someone else.")
    db.refresh(appt)
    return appt