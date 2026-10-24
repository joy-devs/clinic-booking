from datetime import datetime
from pydantic import BaseModel

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime  # if no timezone is given, Nairobi time (EAT) is assumed