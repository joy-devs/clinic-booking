from datetime import datetime, date, time, timedelta, timezone
from app import models

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