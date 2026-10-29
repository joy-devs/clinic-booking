def spec(client):
    return client.get("/openapi.json").json()


def test_patients_group_comes_before_appointments(client):
    names = [t["name"] for t in spec(client)["tags"]]
    assert names.index("patients") < names.index("appointments")


def test_patients_paths_come_before_appointments_paths(client):
    paths = list(spec(client)["paths"])
    first_patient = min(i for i, p in enumerate(paths) if p.startswith("/patients"))
    first_appointment = min(i for i, p in enumerate(paths) if p.startswith("/appointments"))
    assert first_patient < first_appointment


def test_start_comes_before_end_in_every_form(client):
    schemas = spec(client)["components"]["schemas"]
    for name in ("LeaveCreate", "BlockedSlotCreate", "WorkingHoursIn"):
        keys = list(schemas[name]["examples"][0])
        start = next(k for k in keys if k.startswith("start"))
        end = next(k for k in keys if k.startswith("end"))
        assert keys.index(start) < keys.index(end), name


def test_doctor_form_working_hours_start_before_end(client):
    example = spec(client)["components"]["schemas"]["DoctorCreate"]["examples"][0]
    keys = list(example["working_hours"][0])
    assert keys == ["weekday", "start_time", "end_time"]


def test_responses_list_start_before_end(client):
    from datetime import datetime, timedelta, timezone
    eat = timezone(timedelta(hours=3))
    day = datetime.now(eat).date() + timedelta(days=21)
    leave = client.post("/doctors/1/leave", json={
        "start_date": str(day), "end_date": str(day), "reason": "Annual leave"}).json()
    keys = list(leave)
    assert keys.index("start_date") < keys.index("end_date")