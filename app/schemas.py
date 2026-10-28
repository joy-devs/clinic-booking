from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: Optional[datetime] = None  # if no timezone is given, Nairobi time (EAT) is assumed
    slot_id: Optional[str] = None          # e.g. "1-20261103T0900"

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