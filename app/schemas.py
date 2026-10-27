from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime  # if no timezone is given, Nairobi time (EAT) is assumed


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