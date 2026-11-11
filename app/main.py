from fastapi import FastAPI, Request, Security
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from app.database import Base, engine
from app import models
from app.routers import doctors, patients, appointments, leave, auth_routes, observability_routes
from app.schemas import FORM_EXAMPLES
from app.services.booking import BookingError
from app.middleware import add_observability_middleware
from app.auth import verify_api_key

Base.metadata.create_all(bind=engine)

# The order here is the order the groups appear in the API docs.
TAGS = [
    {"name": "doctors"},
    {"name": "patients"},
    {"name": "appointments"},
    {"name": "leave"},
    {"name": "authentication"},
    {"name": "observability"},
]

app = FastAPI(title="Clinic Booking API", openapi_tags=TAGS)

# 1. Initialize and expose Prometheus metrics at /metrics (Public)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# 2. Register Structured Logging & Observability Middleware
app.middleware("http")(add_observability_middleware)


# ==========================================
# PUBLIC ENDPOINTS & ROUTERS
# ==========================================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok"}


# Patients registration remains fully public
app.include_router(patients.router)

# Authentication routes (Login & Logout)
app.include_router(auth_routes.router)

# Observability and Insights hub routes
app.include_router(observability_routes.router)


# ==========================================
# HYBRID & PROTECTED ROUTERS
# ==========================================

# Doctors: GET is public for browsing, POST/DELETE are secured in the router
app.include_router(doctors.router)

# Appointments and Leave: Fully protected with API key
app.include_router(
    appointments.router, 
    dependencies=[Security(verify_api_key)]
)

app.include_router(
    leave.router, 
    dependencies=[Security(verify_api_key)]
)


# ==========================================
# OPENAPI & EXCEPTION HANDLERS
# ==========================================

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