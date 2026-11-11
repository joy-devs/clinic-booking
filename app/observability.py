from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

def setup_observability(app: FastAPI):
    """
    Initializes Prometheus metrics instrumentation for the FastAPI application.
    Exposes metrics at the /metrics endpoint.
    """
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)