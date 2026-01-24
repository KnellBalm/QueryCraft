from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

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
