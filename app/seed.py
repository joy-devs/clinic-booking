from datetime import datetime, time, timedelta
from app.database import Base, engine, SessionLocal
from app import models
from app.services.booking import BookingError, create_leave, EAT

DOCTORS = [
    ("Dr. Amina Odhiambo", "General Practice"),
    ("Dr. Brian Kamau", "Pediatrics"),
    ("Dr. Grace Mwangi", "Dermatology"),
    ("Dr. Peter Otieno", "Cardiology"),
    ("Dr. Faith Njeri", "Gynecology"),
]

# Weekend rota: doctor name -> list of (weekday, start, end).
# Weekday numbers: 5 = Saturday, 6 = Sunday. Each doctor works one weekend day.
WEEKEND_ROTA = {
    "Dr. Amina Odhiambo": [(5, time(8, 0), time(13, 0))],
    "Dr. Brian Kamau": [(5, time(8, 0), time(13, 0))],
    "Dr. Grace Mwangi": [(5, time(8, 0), time(13, 0))],
    "Dr. Peter Otieno": [(6, time(9, 0), time(13, 0))],
    "Dr. Faith Njeri": [(6, time(9, 0), time(13, 0))],
}


def seed_weekend_hours(db):
    """Add weekend shifts for the rota doctors. Safe to run again: a doctor who
    already has hours on a weekday is left alone, so nothing is overwritten."""
    added = 0
    for name, shifts in WEEKEND_ROTA.items():
        doctor = db.query(models.Doctor).filter_by(name=name).first()
        if not doctor:
            continue
        for weekday, start, end in shifts:
            exists = db.query(models.WorkingHours).filter_by(
                doctor_id=doctor.id, weekday=weekday).first()
            if exists:
                continue
            db.add(models.WorkingHours(doctor_id=doctor.id, weekday=weekday,
                                       start_time=start, end_time=end))
            added += 1
    if added:
        db.commit()
        print(f"Added {added} weekend shifts.")
    return added


def seed_leave(db):
    """Starting roster: each doctor gets one leave day, on consecutive weekdays.
    The clinic replaces these with real dates using the leave endpoints."""
    # Relabel rows created earlier with the old "(sample data)" wording
    old = (db.query(models.DoctorLeave)
           .filter(models.DoctorLeave.reason.like("%(sample data)")).all())
    for row in old:
        row.reason = "Annual leave"
    if old:
        db.commit()
        print(f"Relabelled {len(old)} leave entries.")
    if db.query(models.DoctorLeave).count() > 0:
        return
    day = datetime.now(EAT).date() + timedelta(days=14)
    for doctor in db.query(models.Doctor).order_by(models.Doctor.id).all():
        for _ in range(10):
            while day.weekday() > 4:  # skip weekends
                day += timedelta(days=1)
            try:
                create_leave(db, doctor.id, day, day, "Annual leave")
                day += timedelta(days=1)
                break
            except BookingError:  # e.g. a booking already exists that day
                day += timedelta(days=1)
    print("Seeded leave days.")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Doctor).count() == 0:
            for name, specialty in DOCTORS:
                doctor = models.Doctor(name=name, specialty=specialty)
                db.add(doctor)
                db.flush()
                for weekday in range(5):  # Monday to Friday
                    db.add(models.WorkingHours(
                        doctor_id=doctor.id, weekday=weekday,
                        start_time=time(8, 0), end_time=time(17, 0)))
            db.add(models.Patient(name="Test Patient", phone="0700000000"))
            db.commit()
            print("Seeded 5 doctors and 1 patient.")
        else:
            print("Already seeded.")
        seed_weekend_hours(db)
        seed_leave(db)
    finally:
        db.close()


if __name__ == "__main__":
    seed()