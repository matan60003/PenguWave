import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

correlation_id_ctx: ContextVar[str | None] = ContextVar(
    "correlation_id_ctx", default=None
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check if the frontend sent an X-Correlation-ID header
        correlation_id = request.headers.get("X-Correlation-ID")

        # If not, generate a new one
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set the context variable for the duration of the request
        token = correlation_id_ctx.set(correlation_id)

        try:
            response = await call_next(request)
            # Attach it to the response headers so the client knows the ID
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Reset the context variable when the request is done
            correlation_id_ctx.reset(token)
