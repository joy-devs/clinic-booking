# Clinic Booking API

A REST API for booking appointments at a small clinic, built with
FastAPI, SQLAlchemy and PostgreSQL.

## 1. System Design

### Models
- **Doctor**: a clinic doctor (name, specialty).
- **Patient**: a person who books (name, phone).
- **WorkingHours**: the weekday and start/end time a doctor works.
  One doctor can have several rows (one per working day).
- **Appointment**: links a doctor and a patient to a start time and
  end time, with a status (`booked` or `cancelled`) and an optional
  cancel reason.

### Components
- **API layer (routers):** handles HTTP requests and responses.
- **Service layer (`services/booking.py`):** holds all booking rules.
  Book, cancel and reschedule share it so the rules never drift apart.
- **Data layer:** SQLAlchemy models and the PostgreSQL database.

### Key decisions and trade-offs
1. **Slots are calculated, not stored.**
   Availability = the doctor's working hours split into 30-minute
   slots, minus active appointments.
   *Why:* nothing to generate or clean up, and changing a doctor's
   hours doesn't require changing existing data.
   *Trade-off:* it is recalculated on every request. That is fine for
   5 doctors and can be cached if the clinic grows.
2. **Cancelled appointments are kept, not deleted.**
   They stay with status `cancelled` and a reason, which preserves
   history. A cancelled appointment no longer blocks its slot.
3. **Double booking is prevented in two places.**
   The service checks the slot is free and returns `409 Conflict`
   if not. A partial unique index in PostgreSQL (one `booked`
   appointment per doctor and start time) catches the case where two
   requests arrive at the same moment.
   *Trade-off:* the database handles concurrency for us, but we must
   catch the resulting error and turn it into a clean 409.
4. **Reschedule reuses the booking validation.**
   The new slot is checked exactly like a fresh booking, and the
   original slot is freed only if the move succeeds.
5. **PostgreSQL over MySQL.**
   Partial unique indexes make the double-booking safeguard simple,
   and it is a good fit for a system that is expected to grow.
6. **All times are stored in UTC.**
   The clinic is in Nairobi (UTC+3), so working hours are interpreted
   in that timezone and converted.

### Assumptions
- Working hours are 08:00-17:00, Monday to Friday, seeded for 5 doctors.
- Slots are 30 minutes and start on :00 or :30.
- No patient login or authentication (out of scope for this task).
- Booking a time in the past is rejected.

### Built for growth
- New doctors are added as data, with no code changes.
- Later additions: authentication, email/SMS reminders, doctor
  leave and breaks, caching availability, Alembic migrations.