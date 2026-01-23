from starlette.types import ASGIApp, Receive, Scope, Send

class PathRewriteMiddleware:
    """
    Middleware to rewrite paths for requests missing the /api prefix.
    This handles cases where the frontend (or proxy) sends requests to /auth, /problems, etc.
    instead of /api/auth, /api/problems.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            # Check if path starts with one of our known prefixes but missing /api
            # and verify it doesn't already start with /api (to avoid /api/api/...)
            prefixes = ("/auth", "/daily", "/sql", "/problems", "/stats", "/admin", "/practice")
            if path.startswith(prefixes) and not path.startswith("/api"):
                scope["path"] = "/api" + path

        await self.app(scope, receive, send)
