from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_monday():
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def add_leave(client, day, end=None):
    return client.post("/doctors/1/leave", json={
        "start_date": str(day), "end_date": str(end or day), "reason": "Annual leave"})


def test_availability_explains_leave(client):
    monday = next_monday()
    add_leave(client, monday)
    body = client.get(f"/doctors/1/availability?date={monday}").json()
    assert body["slots"] == []
    assert "Dr Test is on leave" in body["notice"]


def test_no_notice_when_doctor_is_working(client):
    monday = next_monday()
    body = client.get(f"/doctors/1/availability?date={monday}").json()
    assert body["notice"] is None


def test_booking_error_names_doctor_and_dates(client):
    monday = next_monday()
    tuesday = monday + timedelta(days=1)
    add_leave(client, monday, tuesday)
    start = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=EAT).isoformat()
    r = client.post("/appointments", json={
        "doctor_id": 1, "patient_id": 1, "start_time": start})
    assert r.status_code == 409
    assert "Dr Test is on leave from" in r.json()["detail"]
    assert str(tuesday) in r.json()["detail"]


def test_notice_lists_other_doctors_working(client):
    monday = next_monday()
    client.post("/doctors", json={
        "name": "Dr Other", "specialty": "GP",
        "working_hours": [{"weekday": 0, "start_time": "08:00:00", "end_time": "17:00:00"}]})
    add_leave(client, monday)
    body = client.get(f"/doctors/1/slots?date={monday}").json()
    assert "Doctors working that day: Dr Other." in body["notice"]