from datetime import datetime, timezone
from sqlalchemy import (Column, Integer, String, DateTime, Date, Time,
                        ForeignKey, Index, text)
from sqlalchemy.orm import relationship
from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    specialty = Column(String)
    working_hours = relationship("WorkingHours", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)


class WorkingHours(Base):
    __tablename__ = "working_hours"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Mon ... 6=Sun
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    doctor = relationship("Doctor", back_populates="working_hours")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="booked")
    cancel_reason = Column(String)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # One *active* booking per doctor per slot
        Index("uq_active_slot", "doctor_id", "start_time", unique=True,
              postgresql_where=text("status = 'booked'"),
              sqlite_where=text("status = 'booked'")),
    )


class BlockedSlot(Base):
    """A period when a doctor is unavailable (lunch, break)."""
    __tablename__ = "blocked_slots"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String)


class DoctorLeave(Base):
    """Whole days when a doctor is on leave (both dates inclusive)."""
    __tablename__ = "doctor_leave"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String)