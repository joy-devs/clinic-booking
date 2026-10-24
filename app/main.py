from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import doctors

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Booking API")
app.include_router(doctors.router)

@app.get("/health")
def health():
    return {"status": "ok"}