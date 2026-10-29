from datetime import datetime, time, timedelta, timezone

from app import models
from app.seed import WEEKEND_ROTA, seed_weekend_hours

EAT = timezone(timedelta(hours=3))


def add_rota_doctors(db):
    ids = {}
    for name in WEEKEND_ROTA:
        doctor = models.Doctor(name=name, specialty="GP")
        db.add(doctor)
        db.flush()
        for weekday in range(5):
            db.add(models.WorkingHours(doctor_id=doctor.id, weekday=weekday,
                                       start_time=time(8, 0), end_time=time(17, 0)))
        ids[name] = doctor.id
    db.commit()
    return ids


def weekdays_of(db, doctor_id):
    rows = db.query(models.WorkingHours).filter_by(doctor_id=doctor_id).all()
    return {r.weekday: (r.start_time, r.end_time) for r in rows}


def test_each_rota_doctor_gets_one_weekend_day(db):
    ids = add_rota_doctors(db)
    assert seed_weekend_hours(db) == 5
    saturday = weekdays_of(db, ids["Dr. Amina Odhiambo"])
    sunday = weekdays_of(db, ids["Dr. Peter Otieno"])
    assert saturday[5] == (time(8, 0), time(13, 0)) and 6 not in saturday
    assert sunday[6] == (time(9, 0), time(13, 0)) and 5 not in sunday


def test_weekend_seed_is_safe_to_run_twice(db):
    add_rota_doctors(db)
    assert seed_weekend_hours(db) == 5
    assert seed_weekend_hours(db) == 0


def test_weekend_seed_does_not_overwrite_existing_hours(db):
    ids = add_rota_doctors(db)
    amina = ids["Dr. Amina Odhiambo"]
    db.add(models.WorkingHours(doctor_id=amina, weekday=5,
                               start_time=time(10, 0), end_time=time(12, 0)))
    db.commit()
    seed_weekend_hours(db)
    assert weekdays_of(db, amina)[5] == (time(10, 0), time(12, 0))


def test_saturday_has_bookable_slots_after_seed(client, db):
    ids = add_rota_doctors(db)
    seed_weekend_hours(db)
    day = datetime.now(EAT).date() + timedelta(days=7)
    while day.weekday() != 5:
        day += timedelta(days=1)
    doctor_id = ids["Dr. Amina Odhiambo"]
    slots = client.get(f"/doctors/{doctor_id}/availability?date={day}").json()["slots"]
    assert len(slots) == 10  # 08:00 to 13:00 in 30-minute slots