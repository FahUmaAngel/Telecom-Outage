"""
Unified Logging and Error Handling Middleware.
"""
import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import traceback

logger = logging.getLogger("TelecomAPI")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log request
        logger.info(f"RID: {request_id} | START | {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            logger.info(f"RID: {request_id} | END | Status: {response.status_code} | Time: {process_time:.2f}ms")
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"RID: {request_id} | ERROR | {str(e)} | Time: {process_time:.2f}ms")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Internal Server Error",
                    "request_id": request_id,
                    "detail": str(e) if logging.DEBUG else "Please contact support"
                }
            )
