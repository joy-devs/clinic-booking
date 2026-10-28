from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_monday():
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def at(hour, minute=0):
    d = next_monday()
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=EAT).isoformat()


def block(client, start_hour, end_hour, doctor_id=1):
    return client.post(f"/doctors/{doctor_id}/blocked-slots", json={
        "start_time": at(start_hour), "end_time": at(end_hour), "reason": "Lunch"})


def day_slots(client):
    return client.get(f"/doctors/1/slots?date={next_monday()}").json()["slots"]


def test_block_marks_slots_blocked(client):
    assert block(client, 12, 13).status_code == 201
    blocked = [s for s in day_slots(client) if s["status"] == "blocked"]
    assert len(blocked) == 2  # 12:00 and 12:30


def test_blocked_slots_leave_availability(client):
    block(client, 12, 13)
    r = client.get(f"/doctors/1/availability?date={next_monday()}")
    assert len(r.json()["slots"]) == 16  # 18 slots minus the 2 blocked


def test_booking_inside_block_rejected(client):
    block(client, 12, 13)
    r = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "start_time": at(12)})
    assert r.status_code == 409


def test_cannot_block_over_booked_appointment(client):
    client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "start_time": at(10)})
    assert block(client, 10, 11).status_code == 409


def test_delete_block_frees_slots(client):
    block_id = block(client, 12, 13).json()["blocked_slot_id"]
    r = client.delete(f"/doctors/1/blocked-slots/{block_id}")
    assert r.status_code == 200
    assert all(s["status"] == "available" for s in day_slots(client))


def test_block_end_before_start_rejected(client):
    assert block(client, 13, 12).status_code == 400


def test_block_unknown_doctor(client):
    assert block(client, 12, 13, doctor_id=99).status_code == 404