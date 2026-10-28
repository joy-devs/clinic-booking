from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_monday():
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def slots_for(client):
    r = client.get(f"/doctors/1/slots?date={next_monday()}")
    assert r.status_code == 200
    return r.json()["slots"]


def slot_at(client, hour):
    suffix = f"T{hour:02d}:00:00+03:00"
    return next(s for s in slots_for(client) if s["start"].endswith(suffix))


def test_slots_cover_whole_day_with_unique_ids(client):
    slots = slots_for(client)
    assert len(slots) == 18  # 08:00 to 17:00 in 30-minute slots
    assert len({s["slot_id"] for s in slots}) == 18
    assert all(s["status"] == "available" for s in slots)


def test_book_by_slot_id_marks_slot_booked(client):
    slot = slot_at(client, 10)
    r = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "slot_id": slot["slot_id"]})
    assert r.status_code == 201
    assert r.json()["slot_id"] == slot["slot_id"]
    status = {s["slot_id"]: s["status"] for s in slots_for(client)}
    assert status[slot["slot_id"]] == "booked"


def test_cancel_makes_slot_available_again(client):
    slot = slot_at(client, 11)
    appt = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "slot_id": slot["slot_id"]}).json()
    client.patch(f"/appointments/{appt['appointment_id']}/cancel", json={"reason": "Schedule conflict"})
    status = {s["slot_id"]: s["status"] for s in slots_for(client)}
    assert status[slot["slot_id"]] == "available"


def test_invalid_slot_id_rejected(client):
    r = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "slot_id": "not-a-slot"})
    assert r.status_code == 400


def test_must_send_exactly_one_of_time_or_slot(client):
    r = client.post("/appointments", json={"doctor_id": 1, "patient_id": 1})
    assert r.status_code == 422