from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_monday():
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def at(day, hour):
    return datetime(day.year, day.month, day.day, hour, 0, tzinfo=EAT).isoformat()


def add_leave(client, start, end, doctor_id=1):
    return client.post(f"/doctors/{doctor_id}/leave", json={
        "start_date": str(start), "end_date": str(end), "reason": "Annual leave"})


def slots_on(client, day):
    return client.get(f"/doctors/1/slots?date={day}").json()["slots"]


def test_leave_marks_whole_day_on_leave(client):
    monday = next_monday()
    assert add_leave(client, monday, monday).status_code == 201
    slots = slots_on(client, monday)
    assert len(slots) == 18
    assert all(s["status"] == "on_leave" for s in slots)
    r = client.get(f"/doctors/1/availability?date={monday}")
    assert r.json()["slots"] == []


def test_booking_on_leave_rejected(client):
    monday = next_monday()
    add_leave(client, monday, monday)
    r = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "start_time": at(monday, 10)})
    assert r.status_code == 409


def test_cannot_add_leave_over_booking(client):
    monday = next_monday()
    client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "start_time": at(monday, 10)})
    assert add_leave(client, monday, monday).status_code == 409


def test_multi_day_leave(client):
    monday = next_monday()
    tuesday = monday + timedelta(days=1)
    wednesday = monday + timedelta(days=2)
    assert add_leave(client, monday, tuesday).status_code == 201
    assert all(s["status"] == "on_leave" for s in slots_on(client, tuesday))
    assert all(s["status"] == "available" for s in slots_on(client, wednesday))


def test_overlapping_leave_rejected(client):
    monday = next_monday()
    add_leave(client, monday, monday)
    assert add_leave(client, monday, monday).status_code == 409


def test_delete_leave_restores_slots(client):
    monday = next_monday()
    leave_id = add_leave(client, monday, monday).json()["leave_id"]
    assert client.delete(f"/doctors/1/leave/{leave_id}").status_code == 200
    assert all(s["status"] == "available" for s in slots_on(client, monday))


def test_leave_end_before_start_rejected(client):
    monday = next_monday()
    assert add_leave(client, monday + timedelta(days=1), monday).status_code == 400


def test_leave_unknown_doctor(client):
    monday = next_monday()
    assert add_leave(client, monday, monday, doctor_id=99).status_code == 404


def test_clinic_wide_leave_list(client):
    monday = next_monday()
    add_leave(client, monday, monday)
    r = client.get(f"/leave?date={monday}")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["doctor_id"] == 1
    assert data[0]["doctor_name"] == "Dr Test"