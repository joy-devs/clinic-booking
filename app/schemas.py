from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

# Fill-in templates shown in the API docs (Swagger). They tell the user what to
# enter; they are not real values. Keys are listed in the order the form should
# show them (start before end). main.py applies these to the API docs.
FORM_EXAMPLES = {
    "AppointmentCreate": {
        "doctor_id": "Enter doctor id",
        "patient_id": "Enter patient id",
        "start_time": "Enter date and time, e.g. 2026-11-11T09:30:00+03:00",
    },
    "CancelRequest": {
        "reason": "Enter reason for cancelling",
    },
    "RescheduleRequest": {
        "start_time": "Enter new date and time, e.g. 2026-11-11T09:30:00+03:00",
    },
    "WorkingHoursIn": {
        "weekday": "Enter weekday number (0 = Monday ... 6 = Sunday)",
        "start_time": "Enter start time, e.g. 08:00:00",
        "end_time": "Enter end time, e.g. 17:00:00",
    },
    "DoctorCreate": {
        "name": "Enter doctor full name",
        "specialty": "Enter specialty",
        "working_hours": [{
            "weekday": "Enter weekday number (0 = Monday ... 6 = Sunday)",
            "start_time": "Enter start time, e.g. 08:00:00",
            "end_time": "Enter end time, e.g. 17:00:00",
        }],
    },
    "PatientCreate": {
        "name": "Enter patient full name",
        "phone": "Enter phone number",
    },
    "BlockedSlotCreate": {
        "start_time": "Enter start date and time, e.g. 2026-11-11T12:00:00+03:00",
        "end_time": "Enter end date and time, e.g. 2026-11-11T13:00:00+03:00",
        "reason": "Enter reason, e.g. Lunch break",
    },
    "LeaveCreate": {
        "start_date": "Enter first day of leave, e.g. 2026-11-11",
        "end_date": "Enter last day of leave, e.g. 2026-11-11",
        "reason": "Enter reason, e.g. Annual leave",
    },
}


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: Optional[datetime] = None  # if no timezone is given, Nairobi time (EAT) is assumed
    slot_id: Optional[str] = None          # e.g. "1-20261103T0900" (use instead of start_time)

    @model_validator(mode="after")
    def exactly_one_of_time_or_slot(self):
        if (self.start_time is None) == (self.slot_id is None):
            raise ValueError("Provide exactly one of start_time or slot_id.")
        return self


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)


class RescheduleRequest(BaseModel):
    start_time: datetime


class WorkingHoursIn(BaseModel):
    weekday: int = Field(ge=0, le=6)  # 0 = Monday ... 6 = Sunday
    start_time: time
    end_time: time


class DoctorCreate(BaseModel):
    name: str = Field(min_length=1)
    specialty: Optional[str] = None
    working_hours: List[WorkingHoursIn] = Field(min_length=1)


class PatientCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: Optional[str] = None


class BlockedSlotCreate(BaseModel):
    start_time: datetime  # if no timezone is given, Nairobi time (EAT) is assumed
    end_time: datetime
    reason: Optional[str] = None


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date  # inclusive; use the same date for a single day
    reason: Optional[str] = None