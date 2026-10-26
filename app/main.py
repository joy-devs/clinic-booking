from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import Base, engine
from app import models
from app.routers import doctors, appointments, patients
from app.services.booking import BookingError

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Booking API")
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(patients.router)


@app.exception_handler(BookingError)
async def booking_error_handler(request: Request, exc: BookingError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
def health():
    return {"status": "ok"}