from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request
from backend.common.logging import get_logger

class PathRewriteMiddleware(BaseHTTPMiddleware):
    """
    Rewrite paths for backward compatibility or convenience.
    Prepends /api to specific paths if missing.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api"):
            for prefix in ["/auth", "/problems", "/sql", "/stats", "/admin", "/practice", "/daily"]:
                if path.startswith(prefix):
                    request.scope["path"] = "/api" + path
                    break

        response = await call_next(request)
        return response

class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch unhandled exceptions and return a JSON response with 500 status code.
    This ensures that CORS middleware can still add headers to the response.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger = get_logger("backend.middleware.exception")
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )

class CORSLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log CORS related headers to help debugging.
    Should be placed OUTSIDE CORSMiddleware.
    """
    async def dispatch(self, request: Request, call_next):
        logger = get_logger("backend.middleware.cors")
        origin = request.headers.get("origin")

        # Log incoming origin
        if origin:
            logger.info(f"CORS Request from Origin: {origin} -> {request.method} {request.url.path}")

        response = await call_next(request)

        # Check for CORS headers in response if origin was present
        if origin:
            allow_origin = response.headers.get("access-control-allow-origin")
            if not allow_origin:
                logger.warning(f"CORS Warning: No Access-Control-Allow-Origin header in response for origin: {origin}. Status: {response.status_code}")
            else:
                 logger.debug(f"CORS Success: Access-Control-Allow-Origin: {allow_origin}")

        return response
