from datetime import datetime, timedelta, timezone

EAT = timezone(timedelta(hours=3))


def next_weekday(weekday):
    d = datetime.now(EAT).date() + timedelta(days=7)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def hours(weekday=1, start="10:00:00", end="12:00:00"):
    return {"weekday": weekday, "start_time": start, "end_time": end}


def test_set_working_hours_changes_availability(client):
    r = client.post("/doctors/1/working-hours", json=hours())
    assert r.status_code == 200
    day = next_weekday(1)
    slots = client.get(f"/doctors/1/availability?date={day}").json()["slots"]
    assert len(slots) == 4  # 10:00 to 12:00 is four 30-minute slots


def test_working_hours_unknown_doctor(client):
    assert client.post("/doctors/99/working-hours", json=hours()).status_code == 404


def test_working_hours_end_before_start(client):
    r = client.post("/doctors/1/working-hours", json=hours(start="12:00:00", end="10:00:00"))
    assert r.status_code == 422


def test_working_hours_must_be_on_half_hour(client):
    r = client.post("/doctors/1/working-hours", json=hours(start="09:15:00"))
    assert r.status_code == 422


def test_create_patient_and_doctor(client):
    p = client.post("/patients", json={"name": "Mary Wanjiku", "phone": "0711111111"})
    assert p.status_code == 201
    d = client.post("/doctors", json={
        "name": "Dr New", "specialty": "GP",
        "working_hours": [hours(weekday=0, start="09:00:00", end="11:00:00")]})
    assert d.status_code == 201
    day = next_weekday(0)
    slots = client.get(f"/doctors/{d.json()['id']}/availability?date={day}").json()["slots"]
    assert len(slots) == 4