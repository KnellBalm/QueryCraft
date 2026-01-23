import pytest
from starlette.types import Scope, Receive, Send
from backend.common.middleware import PathRewriteMiddleware

@pytest.mark.asyncio
async def test_path_rewrite_middleware():
    async def mock_app(scope: Scope, receive: Receive, send: Send):
        # The middleware calls the app, so this assertion runs inside the middleware call
        assert scope["path"] == "/api/auth/me"

    middleware = PathRewriteMiddleware(mock_app)

    scope = {
        "type": "http",
        "path": "/auth/me",
    }

    await middleware(scope, None, None)

    # Also verify scope was modified in place
    assert scope["path"] == "/api/auth/me"

@pytest.mark.asyncio
async def test_path_rewrite_middleware_no_rewrite():
    async def mock_app(scope: Scope, receive: Receive, send: Send):
        assert scope["path"] == "/api/auth/me"

    middleware = PathRewriteMiddleware(mock_app)

    scope = {
        "type": "http",
        "path": "/api/auth/me",
    }

    await middleware(scope, None, None)

    assert scope["path"] == "/api/auth/me"

@pytest.mark.asyncio
async def test_path_rewrite_middleware_ignore_other():
    async def mock_app(scope: Scope, receive: Receive, send: Send):
        assert scope["path"] == "/other"

    middleware = PathRewriteMiddleware(mock_app)

    scope = {
        "type": "http",
        "path": "/other",
    }

    await middleware(scope, None, None)

    assert scope["path"] == "/other"
