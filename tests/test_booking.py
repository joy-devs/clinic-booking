from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_monday():
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def slot(hour, minute=0):
    d = next_monday()
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=EAT).isoformat()


def book(client, start, patient_id=1, doctor_id=1):
    return client.post("/appointments", json={
        "doctor_id": doctor_id, "patient_id": patient_id, "start_time": start})


def free_starts(client):
    r = client.get(f"/doctors/1/availability?date={next_monday()}")
    return [s["start"] for s in r.json()["slots"]]


def test_book_success(client):
    r = book(client, slot(9))
    assert r.status_code == 201
    assert r.json()["status"] == "booked"


def test_double_booking_rejected(client):
    book(client, slot(9))
    r = book(client, slot(9), patient_id=2)
    assert r.status_code == 409


def test_outside_working_hours(client):
    assert book(client, slot(7)).status_code == 400
    assert book(client, slot(17)).status_code == 400


def test_must_be_on_half_hour(client):
    assert book(client, slot(9, 15)).status_code == 400


def test_past_time_rejected(client):
    assert book(client, "2020-01-06T09:00:00+03:00").status_code == 400


def test_unknown_doctor(client):
    assert book(client, slot(9), doctor_id=99).status_code == 404


def test_booked_slot_leaves_availability(client):
    assert slot(9) in free_starts(client)
    book(client, slot(9))
    assert slot(9) not in free_starts(client)


def test_cancel_frees_slot_for_rebooking(client):
    appt_id = book(client, slot(9)).json()["id"]
    r = client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "Unwell"})
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert book(client, slot(9), patient_id=2).status_code == 201


def test_cancel_twice_fails(client):
    appt_id = book(client, slot(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "Unwell"})
    r = client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "Again"})
    assert r.status_code == 409


def test_reschedule_frees_original_slot(client):
    appt_id = book(client, slot(9)).json()["id"]
    r = client.patch(f"/appointments/{appt_id}/reschedule",
                     json={"start_time": slot(10)})
    assert r.status_code == 200
    starts = free_starts(client)
    assert slot(9) in starts
    assert slot(10) not in starts


def test_reschedule_cancelled_fails(client):
    appt_id = book(client, slot(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "Unwell"})
    r = client.patch(f"/appointments/{appt_id}/reschedule",
                     json={"start_time": slot(10)})
    assert r.status_code == 409


def test_reschedule_to_taken_slot_fails(client):
    first = book(client, slot(9)).json()["id"]
    book(client, slot(10), patient_id=2)
    r = client.patch(f"/appointments/{first}/reschedule",
                     json={"start_time": slot(10)})
    assert r.status_code == 409


def test_booking_within_one_hour_rejected(client):
    soon = (datetime.now(EAT) + timedelta(minutes=20)).replace(second=0, microsecond=0)
    soon = soon.replace(minute=0 if soon.minute < 30 else 30)
    assert book(client, soon.isoformat()).status_code == 400


def test_patient_upcoming_sorted(client):
    book(client, slot(11))
    book(client, slot(9))
    r = client.get("/patients/1/appointments")
    assert r.status_code == 200
    starts = [a["start"] for a in r.json()]
    assert starts == sorted(starts)
    assert len(starts) == 2