def test_list_patients_starts_with_existing(client):
    r = client.get("/patients")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert names == ["Patient One", "Patient Two"]


def test_created_patient_appears_in_list(client):
    created = client.post("/patients", json={"name": "Mary Wanjiku", "phone": "0711111111"})
    assert created.status_code == 201
    patient_id = created.json()["patient_id"]
    listed = client.get("/patients").json()
    assert listed[-1] == {"patient_id": patient_id, "name": "Mary Wanjiku",
                          "phone": "0711111111"}
    assert len(listed) == 3


def test_patient_list_is_ordered_by_id(client):
    client.post("/patients", json={"name": "Zed", "phone": "1"})
    client.post("/patients", json={"name": "Amy", "phone": "2"})
    ids = [p["patient_id"] for p in client.get("/patients").json()]
    assert ids == sorted(ids)