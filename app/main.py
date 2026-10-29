from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from app.database import Base, engine
from app import models
from app.routers import doctors, patients, appointments, leave
from app.schemas import FORM_EXAMPLES
from app.services.booking import BookingError

Base.metadata.create_all(bind=engine)

# The order here is the order the groups appear in the API docs.
TAGS = [
    {"name": "doctors"},
    {"name": "patients"},
    {"name": "appointments"},
    {"name": "leave"},
]

app = FastAPI(title="Clinic Booking API", openapi_tags=TAGS)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(leave.router)


def custom_openapi():
    """Build the API docs, then put our form templates in with their keys in order."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version,
                         description=app.description, routes=app.routes,
                         tags=app.openapi_tags)
    components = schema.get("components", {}).get("schemas", {})
    for name, example in FORM_EXAMPLES.items():
        if name in components:
            components[name]["examples"] = [example]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.exception_handler(BookingError)
async def booking_error_handler(request: Request, exc: BookingError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}