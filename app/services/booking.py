from datetime import datetime, date, time, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from app import models

EAT = timezone(timedelta(hours=3))  # Nairobi, no daylight saving
SLOT = timedelta(minutes=30)


class BookingError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def as_utc(dt: datetime) -> datetime:
    # SQLite returns naive datetimes; we always store UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    # Input without a timezone is treated as Nairobi time
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
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


def validate_slot(db, doctor_id: int, start: datetime):
    local = start.astimezone(EAT)
    if local.minute % 30 != 0 or local.second or local.microsecond:
        raise BookingError(400, "Appointments must start on the hour or half hour.")
    if start <= datetime.now(timezone.utc):
        raise BookingError(400, "Cannot book a time in the past.")
    if start < datetime.now(timezone.utc) + timedelta(hours=1):
        raise BookingError(400, "Appointments must be booked at least 1 hour in advance.")

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


def cancel_appointment(db, appointment_id: int, reason: str):
    appt = db.get(models.Appointment, appointment_id)
    if not appt:
        raise BookingError(404, "Appointment not found.")
    if appt.status == "cancelled":
        raise BookingError(409, "Appointment is already cancelled.")
    appt.status = "cancelled"
    appt.cancel_reason = reason
    db.commit()
    db.refresh(appt)
    return appt


def reschedule_appointment(db, appointment_id: int, new_start: datetime):
    appt = db.get(models.Appointment, appointment_id)
    if not appt:
        raise BookingError(404, "Appointment not found.")
    if appt.status == "cancelled":
        raise BookingError(409, "Cannot reschedule a cancelled appointment.")

    new_start = to_utc(new_start)
    if new_start == as_utc(appt.start_time):
        raise BookingError(400, "Appointment is already at that time.")
    validate_slot(db, appt.doctor_id, new_start)  # same rules as a fresh booking

    appt.start_time = new_start
    appt.end_time = new_start + SLOT
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BookingError(409, "That slot was just booked by someone else.")
    db.refresh(appt)
    return appt