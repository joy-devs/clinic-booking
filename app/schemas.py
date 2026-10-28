from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

EAT = timezone(timedelta(hours=3))


def example_start(hour: int = 9) -> str:
    """A valid example time: a weekday at least 2 days ahead, Nairobi time."""
    d = datetime.now(EAT).date() + timedelta(days=2)
    while d.weekday() > 4:  # skip Saturday and Sunday
        d += timedelta(days=1)
    return datetime(d.year, d.month, d.day, hour, 0, tzinfo=EAT).isoformat()


def example_date(days_ahead: int = 7) -> str:
    d = datetime.now(EAT).date() + timedelta(days=days_ahead)
    while d.weekday() > 4:
        d += timedelta(days=1)
    return d.isoformat()


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: Optional[datetime] = None  # if no timezone is given, Nairobi time (EAT) is assumed
    slot_id: Optional[str] = None          # e.g. "1-20261103T0900" (use instead of start_time)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"doctor_id": 1, "patient_id": 1, "start_time": example_start()}
    ]})

    @model_validator(mode="after")
    def exactly_one_of_time_or_slot(self):
        if (self.start_time is None) == (self.slot_id is None):
            raise ValueError("Provide exactly one of start_time or slot_id.")
        return self


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"reason": "Schedule conflict"}
    ]})


class RescheduleRequest(BaseModel):
    start_time: datetime

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"start_time": example_start(10)}
    ]})


class WorkingHoursIn(BaseModel):
    weekday: int = Field(ge=0, le=6)  # 0 = Monday ... 6 = Sunday
    start_time: time
    end_time: time

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"weekday": 1, "start_time": "10:00:00", "end_time": "12:00:00"}
    ]})


class DoctorCreate(BaseModel):
    name: str = Field(min_length=1)
    specialty: Optional[str] = None
    working_hours: List[WorkingHoursIn] = Field(min_length=1)

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"name": "Dr. Jane Doe", "specialty": "General Practice",
         "working_hours": [{"weekday": 0, "start_time": "08:00:00", "end_time": "17:00:00"}]}
    ]})


class PatientCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"name": "Patient full name", "phone": "07XXXXXXXX"}
    ]})


class BlockedSlotCreate(BaseModel):
    start_time: datetime  # if no timezone is given, Nairobi time (EAT) is assumed
    end_time: datetime
    reason: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"start_time": example_start(12), "end_time": example_start(13),
         "reason": "Lunch break"}
    ]})


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date  # inclusive; use the same date for a single day
    reason: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"start_date": example_date(7), "end_date": example_date(7),
         "reason": "Annual leave"}
    ]})