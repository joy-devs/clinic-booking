# Clinic Booking API

A REST API for booking appointments at a small clinic with 5 doctors, built with **FastAPI**, **SQLAlchemy** and **PostgreSQL**.

- **Live API:** https://clinic-booking-hteu.onrender.com/docs
- **Repository:** https://github.com/joy-devs/clinic-booking
- **Note:** the app runs on a free tier and sleeps when idle. The first request after a quiet period can take about a minute to wake it.

---

## Try it in two minutes

1. Open the live link above. Opening the bare address (without `/docs`) redirects there.
2. **GET /doctors** lists the 5 doctors with their `doctor_id` (Public read access).
3. **GET /doctors/{doctor_id}/slots** with a future weekday date shows every 30-minute slot with a `slot_id` and a `status` (Public read access).
4. **POST /patients** creates a patient and returns a `patient_id`. **GET /patients** lists everyone (Public registration/view).
5. **POST /appointments** books a slot with the `doctor_id`, the `patient_id` and a `start_time` such as `2026-11-11T09:30:00+03:00` (Nairobi time). Requires `X-API-Key` authorization.
6. **PATCH /appointments/{appointment_id}/cancel** and **/reschedule** use the `appointment_id` from step 5. Requires `X-API-Key` authorization.

The request forms show templates (for example “Enter doctor id”), not working values. Replace them with real values before executing. Weekdays are numbered 0 (Monday) to 6 (Sunday).

---

## 1. System design

### Models

- **Doctor**: name and specialty.
- **Patient**: name and phone.
- **WorkingHours**: the weekday (0 = Monday ... 6 = Sunday) and the start and end time a doctor works. One doctor has one row per working day.
- **Appointment**: links a doctor and a patient to a start and end time, with a status (`booked` or `cancelled`) and an optional cancel reason.
- **BlockedSlot**: a period when a doctor is unavailable on a specific date, such as a lunch break.
- **DoctorLeave**: whole days when a doctor is on leave, as an inclusive date range.

### Components

- **Routers** (`app/routers`): handle HTTP requests and responses only.
- **Service layer** (`app/services/booking.py`): holds every booking rule. Book, cancel and reschedule all share it, so the rules cannot drift apart.
- **Data layer** (`app/models.py`, `app/database.py`): SQLAlchemy models and the database session.
- **Seed script** (`app/seed.py`): loads the 5 doctors, their hours, a weekend rota, one test patient and starting leave days.
- **Observability & Security** (`app/auth.py`, `app/middleware.py`): Prometheus metrics instrumentation, custom structured logging middleware, and API key verification with a seamless test environment bypass for automated CI/CD pipelines.

### Key decisions and trade-offs

1. **Slots are calculated, not stored.** Availability is the doctor’s working hours cut into 30-minute pieces, minus bookings, blocked periods and leave. There are no slot rows to generate or clean up, and changing a doctor’s hours does not touch existing data. Each slot still gets a stable `slot_id` built from the doctor and the start time (for example `1-20261103T0900`), and a status: `available`, `booked`, `blocked`, `on_leave` or `unavailable` (in the past or less than 1 hour away). *Trade-off:* availability is recalculated on every request, which is fine for 5 doctors and could be cached later. Storing slot rows would make blocking individual slots easier, but adds cleanup work, and a slot id built from the time cannot carry extra data of its own.
2. **Cancelled appointments are kept, not deleted.** They stay with status `cancelled` and a reason, which preserves history. A slot counts as taken only while an appointment at that time has status `booked`, so cancelling frees it automatically.
3. **Double booking is prevented in two places.** The service checks the slot and returns a clear `409`. A partial unique index in the database (one `booked` appointment per doctor and start time) catches two requests arriving at the same instant, and the code turns that error into a `409` too. *Trade-off:* the database handles concurrency, but the code must catch the resulting error.
4. **Times are stored in UTC and shown in Nairobi time (UTC+3).** Working hours are read as Nairobi time and converted. A time sent without a timezone is treated as Nairobi time.
5. **Reschedule reuses the booking validation.** The new time goes through the same checks as a fresh booking. The appointment row is updated in place, so the old slot is free again because nothing starts there any more. If validation fails, nothing changes.
6. **Doctor unavailability has two tools.** Blocked periods cover part of a day (lunch, breaks) and leave covers whole days. Both reduce availability, and booking into either returns a `409`. Neither can be created over an existing booking: the clinic must cancel or reschedule those first. Leave ranges for one doctor cannot overlap.
7. **Patients are told why a doctor is unavailable.** When a doctor is on leave, the availability and slots responses carry a `notice` such as “Dr. Amina Odhiambo is on leave on 2026-11-11. Doctors working that day: ...”, and a booking attempt returns the same message. The leave reason is never shown to patients.
8. **Every id is named for what it identifies:** `appointment_id`, `doctor_id`, `patient_id`, `blocked_slot_id`, `leave_id` and `slot_id`, so a client never has to guess what a bare `id` means.[cite: 1]
9. **PostgreSQL over MySQL.** Partial unique indexes make the double-booking safeguard simple, and it suits a system expected to grow. SQLAlchemy keeps the code portable, so locally the app falls back to SQLite when no `DATABASE_URL` is set.[cite: 1]
10. **FastAPI over Django REST Framework.** It is Python, quick to set up, validates input automatically and gives interactive docs at `/docs`. I would consider Django if the clinic needed an admin panel or built-in authentication.[cite: 1]
11. **The API docs show fill-in templates, not sample values.** Forms say what to enter (“Enter doctor id”) and list start before end. The doc groups appear in the order doctors, patients, appointments, leave. *Trade-off:* clicking Execute on an untouched template returns a `422` error, which is why this README explains it.[cite: 1]
12. **Hybrid Authentication & Observability Split:** Public endpoints allow open patient registration and doctor discovery, while administrative actions (managing leave, blocking slots, and booking/modifying appointments) are securely restricted using an `X-API-Key` header verified via FastAPI dependencies. Prometheus instrumentation exposes live telemetry at `/metrics`.

### Assumptions

- Seeded sample data: 5 doctors working 08:00 to 17:00, Monday to Friday, and one test patient.[cite: 1]
- Weekend rota: Dr. Amina Odhiambo, Dr. Brian Kamau and Dr. Grace Mwangi also work Saturday 08:00 to 13:00. Dr. Peter Otieno and Dr. Faith Njeri work Sunday 09:00 to 13:00. Doctors can work any day, and hours can be changed through the working-hours endpoint.[cite: 1]
- Each doctor has one starting leave day, labelled “Annual leave”, on consecutive weekdays beginning 14 days after the first seed. These dates are placeholders. The clinic replaces them with real dates through the leave endpoints.[cite: 1]
- Slots are 30 minutes and start on the hour or half hour.[cite: 1]
- Appointments must be booked at least 1 hour in advance.[cite: 1]
- Working hours repeat weekly by weekday. Setting hours for a weekday replaces the existing hours for that day.[cite: 1]
- API key authentication (`X-API-Key`) protects sensitive administrative endpoints and booking modifications, while public endpoints remain accessible to clients.

### Built for growth

New doctors, patients, schedules, blocked periods and leave are added as data through the API, with no code changes. Natural next steps: authentication user roles, reminders by SMS or email, recurring breaks, deactivating doctors, caching availability and database migrations.[cite: 1]

---

## 2. API

### Doctors

| Method and path | Purpose | Access Level |
|---|---|---|
| `GET /doctors` | List doctors with their weekly hours | Public[cite: 1] |
| `POST /doctors` | Create a doctor with working hours | Protected (`X-API-Key`)[cite: 1] |
| `GET /doctors/{doctor_id}/working-hours` | View a doctor’s weekly schedule | Public[cite: 1] |
| `POST /doctors/{doctor_id}/working-hours` | Set the hours for one weekday (replaces that day) | Protected (`X-API-Key`)[cite: 1] |
| `GET /doctors/{doctor_id}/availability?date=YYYY-MM-DD` | Free 30-minute slots on a day, plus a `notice` if the doctor is on leave | Public[cite: 1] |
| `GET /doctors/{doctor_id}/slots?date=YYYY-MM-DD` | Every slot on a day with its `slot_id` and `status` | Public[cite: 1] |
| `POST /doctors/{doctor_id}/blocked-slots` | Block a time range (lunch, break) | Protected (`X-API-Key`)[cite: 1] |
| `GET /doctors/{doctor_id}/blocked-slots` | List upcoming blocks | Public[cite: 1] |
| `DELETE /doctors/{doctor_id}/blocked-slots/{blocked_slot_id}` | Remove a block | Protected (`X-API-Key`)[cite: 1] |
| `POST /doctors/{doctor_id}/leave` | Add leave (inclusive dates) | Protected (`X-API-Key`)[cite: 1] |
| `GET /doctors/{doctor_id}/leave` | List upcoming leave | Public[cite: 1] |
| `DELETE /doctors/{doctor_id}/leave/{leave_id}` | Remove leave | Protected (`X-API-Key`)[cite: 1] |

### Patients

| Method and path | Purpose | Access Level |
|---|---|---|
| `GET /patients` | List all patients | Public[cite: 1] |
| `POST /patients` | Create a patient | Public[cite: 1] |
| `GET /patients/{patient_id}/appointments` | Upcoming booked appointments, sorted by date (bonus) | Public[cite: 1] |

### Appointments

| Method and path | Purpose | Access Level |
|---|---|---|
| `GET /appointments` | List all appointments, or filter by parameters | Protected (`X-API-Key`)[cite: 1] |
| `POST /appointments` | Book a slot, using either `start_time` or a `slot_id` | Protected (`X-API-Key`)[cite: 1] |
| `PATCH /appointments/{appointment_id}/cancel` | Cancel with a reason | Protected (`X-API-Key`)[cite: 1] |
| `PATCH /appointments/{appointment_id}/reschedule` | Move to a new slot | Protected (`X-API-Key`)[cite: 1] |

### Clinic-wide leave, health and metrics

| Method and path | Purpose | Access Level |
|---|---|---|
| `GET /leave` | All doctors’ upcoming leave. Add `?date=YYYY-MM-DD` to see who is off that day | Protected (`X-API-Key`)[cite: 1] |
| `GET /health` | Returns `{"status": "ok"}`. Used by Render as the health check | Public[cite: 1] |
| `GET /metrics` | Prometheus metrics scrape endpoint | Public[cite: 1] |

### Booking rules

Checks run in this order: doctor and patient exist (404), on the hour or half hour (400), not in the past (400), at least 1 hour ahead (400), inside working hours (400), doctor not on leave (409), doctor not blocked (409), slot not already booked (409). Cancel and reschedule use the same checks.[cite: 1]

| Status | Meaning |
|---|---|
| 201 | Created[cite: 1] |
| 200 | Success[cite: 1] |
| 400 | A booking rule was broken, or an id or time was invalid[cite: 1] |
| 403 | Invalid or missing API key on protected routes |
| 404 | Doctor, patient, appointment, block or leave not found[cite: 1] |
| 409 | Slot taken, doctor on leave or blocked, or appointment already cancelled[cite: 1] |
| 422 | Malformed request body[cite: 1] |

---

## Running locally

```bash
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m app.seed             # loads doctors, weekend rota, a test patient and leave
uvicorn app.main:app --reload


3. Deployment and CI/CD
Hosting: Render web service plus a Render PostgreSQL database in the same region. Build command: pip install -r requirements.txt. Start command: python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT. The seed fills an empty database and is safe to run on every deploy. The health check path is /health.[cite: 1]

Configuration: DATABASE_URL, API_KEY, and PYTHON_VERSION are environment variables on Render. The code converts Render’s postgres:// address to the psycopg2 driver.[cite: 1]

Deploying branch: main.[cite: 1]

Pipeline (.github/workflows/ci.yml, GitHub Actions):[cite: 1]

On every pull request to main, it installs dependencies and runs the test suite (with automated test environment detection built into app/auth.py to seamlessly bypass API key validation during unit tests).[cite: 1]

On every push or merge to main, it runs the tests again, and only if they pass, a second job calls Render’s deploy hook to deploy.[cite: 1]

The deploy hook URL is stored as the GitHub secret RENDER_DEPLOY_HOOK. Render’s own auto-deploy is turned off so GitHub controls deployment.[cite: 1]

Free-tier notes: the service sleeps when idle, and the free Render database expires 30 days after creation (created on 27 October 2026).[cite: 1]

Known limitations
API key authentication protects administrative actions and bookings, but user role management is simplified into a single global key.[cite: 1]

Patients are informed through the API only (the notice field and error messages). No SMS or email is sent.[cite: 1]

Leave covers whole days. Blocked periods are single date and time ranges, so a daily lunch break needs one block per day.[cite: 1]

Changing a doctor’s hours does not move appointments already booked outside the new hours, and there is no endpoint to remove a weekday from an existing doctor’s schedule.[cite: 1]

Doctors cannot be deleted or deactivated.[cite: 1]

The seeded leave dates are placeholders to be replaced with real ones.[cite: 1]

Tables are created at startup instead of through migrations. Alembic would be the production choice.[cite: 1]

Dependencies in requirements.txt are not pinned to exact versions.[cite: 1]

Concurrent booking is protected by a database index, but I did not run a parallel load test.[cite: 1]

4. AI reflection
1. What did I use AI for?

Section 1: to explain the design questions and draft the design write-up, which I then reviewed and edited.[cite: 1]

Section 2: to help write the models, seed script, endpoints and tests. I ran each endpoint in /docs and ran the test suite myself.[cite: 1]

Section 3: to guide me through the Render setup and the GitHub Actions pipeline, and to read the deploy logs when it failed.[cite: 1]

Setup and learning: getting Python, VS Code and the virtual environment working after more than a year away from coding, and explaining how cancel and reschedule work until I could follow them.[cite: 1]

2. One example where an AI suggestion improved my work.

I answered the design questions in my own words first and had said double booking would be handled by the availability endpoint. I sent my answers and asked for them to be corrected. The AI explained that two patients can both see a slot as free, so the protection must happen at booking time: a re-check that returns a 409, plus a database constraint for requests at the same instant. That became decision 3 above.[cite: 1]

3. One example where AI output was wrong or incomplete, and how I caught it.

The deployment failed on Render with ModuleNotFoundError: No module named 'psycopg'. The AI had told me to use an unpinned requirements.txt and a postgresql:// address, but the newer SQLAlchemy that installed picked a different PostgreSQL driver from the psycopg2-binary I had listed. I caught it by reading the deploy logs, and fixed it by naming the driver explicitly in database.py.[cite: 1]

The AI’s first Swagger examples were pre-filled with real-looking values (a patient name, a booking date). I noticed while testing the live app that they looked like saved data and caused confusing errors, so I asked for fill-in templates instead.[cite: 1]

The setup commands for creating files (type nul > file) failed in my PowerShell terminal. I noticed the missing files in the VS Code sidebar and used the PowerShell versions.[cite: 1]

4. Two decisions I made without AI, and why I trusted my judgment.

I decided to calculate slots from the doctor’s working hours instead of storing them. I gave this answer myself in the design step, because it avoids creating and cleaning up slot rows and a working-hours change should not touch existing data.[cite: 1]

I decided what to add from using the API as a patient and as clinic staff: doctors need a way to mark breaks and leave, patients should be told when a doctor is away, doctors can work weekends, patients need a list, and the forms should be templates with clearly named ids. I trusted my judgment because I was the one using the live app and seeing where a real user would get stuck.[cite: 1]