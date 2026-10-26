from datetime import datetime
from pydantic import BaseModel, Field

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime  # if no timezone is given, Nairobi time (EAT) is assumed

class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)

class RescheduleRequest(BaseModel):
    start_time: datetime