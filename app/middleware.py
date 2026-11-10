
import time
import logging
from fastapi import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("clinic_api")

async def add_observability_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"Method={request.method} Path={request.url.path} "
        f"Status={response.status_code} Duration={process_time:.4f}s"
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response
