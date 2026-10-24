from datetime import time
from app.database import Base, engine, SessionLocal
from app import models

DOCTORS = [
    ("Dr. Amina Odhiambo", "General Practice"),
    ("Dr. Brian Kamau", "Pediatrics"),
    ("Dr. Grace Mwangi", "Dermatology"),
    ("Dr. Peter Otieno", "Cardiology"),
    ("Dr. Faith Njeri", "Gynecology"),
]

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Doctor).count() > 0:
            print("Already seeded.")
            return
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
    finally:
        db.close()

if __name__ == "__main__":
    seed()