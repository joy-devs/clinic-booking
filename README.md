# Clinic Booking API

A REST API for booking appointments at a small clinic with 5 doctors, built with **FastAPI**, **SQLAlchemy** and **PostgreSQL**.

- **Live API:** https://clinic-booking-hteu.onrender.com/docs
- **Repository:** https://github.com/joy-devs/clinic-booking
- **Note:** the app runs on a free tier and sleeps when idle. The first request after a quiet period can take about a minute to wake it.

---

## 1. System design

### Models

- **Doctor**: name and specialty.
- **Patient**: name and phone.
- **WorkingHours**: the weekday (0 = Monday) and the start and end time a doctor works. One doctor has one row per working day.
- **Appointment**: links a doctor and a patient to a start and end time, with a status (`booked` or `cancelled`) and an optional cancel reason.

### Components

- **Routers** (`app/routers`): handle HTTP requests and responses only.
- **Service layer** (`app/services/booking.py`): holds every booking rule. Book, cancel and reschedule all share it, so the rules cannot drift apart.
- **Data layer** (`app/models.py`, `app/database.py`): SQLAlchemy models and the database session.

### Key decisions and trade-offs

1. **Slots are calculated, not stored.** Availability is the doctor’s working hours cut into 30-minute pieces, minus the appointments that are currently booked. There are no slot rows to generate or clean up, and changing a doctor’s hours does not touch existing data. *Trade-off:* availability is recalculated on every request. That is fine for 5 doctors and could be cached if the clinic grows. Storing slot rows would make blocking individual slots easier, but adds cleanup work.
2. **Cancelled appointments are kept, not deleted.** They stay with status `cancelled` and a reason, which preserves history. A slot counts as taken only while an appointment at that time has status `booked`, so cancelling frees it automatically.
3. **Double booking is prevented in two places.** The service checks the slot and returns a clear `409`. A partial unique index in the database (one `booked` appointment per doctor and start time) catches two requests arriving at the same instant, and the code turns that error into a `409` too. *Trade-off:* the database handles concurrency, but the code must catch the resulting error.
4. **Times are stored in UTC and shown in Nairobi time (UTC+3).** Working hours are read as Nairobi time and converted. A time sent without a timezone is treated as Nairobi time.
5. **Reschedule reuses the booking validation.** The new time goes through the same checks as a fresh booking. The appointment row is updated in place, so the old slot is free again because nothing starts there any more. If validation fails, nothing changes.
6. **PostgreSQL over MySQL.** Partial unique indexes make the double-booking safeguard simple, and it suits a system expected to grow. SQLAlchemy keeps the code portable, so locally the app falls back to SQLite when no `DATABASE_URL` is set.
7. **FastAPI over Django REST Framework.** It is Python, quick to set up, validates input automatically and gives interactive docs at `/docs`. I would consider Django if the clinic needed an admin panel or built-in authentication.

### Assumptions

- Seeded sample data: 5 doctors working 08:00 to 17:00, Monday to Friday, and one test patient.
- Slots are 30 minutes and start on the hour or half hour.
- Appointments must be booked at least 1 hour in advance.
- Working hours repeat weekly by weekday. Setting hours for a weekday replaces the existing hours for that day.
- There is no authentication, so anyone can create records or book for any patient.

### Built for growth

New doctors, patients and schedules are added as data through the API, with no code changes. Natural next steps: authentication, reminders by SMS or email, doctor leave and breaks, caching availability, and database migrations.

---

## 2. API

| Method and path | Purpose |
|---|---|
| `GET /doctors/{id}/availability?date=YYYY-MM-DD` | Free 30-minute slots for a doctor on a day |
| `POST /appointments` | Book a slot |
| `PATCH /appointments/{id}/cancel` | Cancel with a reason |
| `PATCH /appointments/{id}/reschedule` | Move to a new slot |
| `GET /patients/{id}/appointments` | Upcoming booked appointments, sorted by date (bonus) |
| `POST