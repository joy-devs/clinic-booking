from datetime import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app import models


@pytest.fixture()
def db():
    engine = create_engine("sqlite://",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False)()

    doctor = models.Doctor(name="Dr Test", specialty="GP")
    session.add(doctor)
    session.flush()
    for weekday in range(5):
        session.add(models.WorkingHours(doctor_id=doctor.id, weekday=weekday,
                                        start_time=time(8, 0), end_time=time(17, 0)))
    session.add(models.Patient(name="Patient One", phone="1"))
    session.add(models.Patient(name="Patient Two", phone="2"))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    def override():
        yield db
    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()