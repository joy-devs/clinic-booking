import time
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger
logger = logging.getLogger("clinic_app")
logger.setLevel(logging.INFO)

# In-memory log buffer to allow viewing recent logs via API endpoint
RECENT_LOGS = []
MAX_LOG_HISTORY = 50

def get_recent_logs():
    return RECENT_LOGS

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        log_payload = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 4),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        # Keep recent logs in memory for the observability endpoint
        global RECENT_LOGS
        RECENT_LOGS.insert(0, log_payload)
        if len(RECENT_LOGS) > MAX_LOG_HISTORY:
            RECENT_LOGS.pop()
            
        logger.info(json.dumps(log_payload))
        return response