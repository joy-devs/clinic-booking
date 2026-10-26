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