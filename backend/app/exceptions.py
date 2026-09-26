"""
Domain exceptions. Services raise these; `app.api.errors` maps them to HTTP
responses in one place, so business logic never depends on FastAPI.
"""


class AppError(Exception):
    """Base class for expected errors whose `detail` is safe to show users."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class InvalidRequestError(AppError):
    pass


class UnsupportedMediaTypeError(AppError):
    pass


class PayloadTooLargeError(AppError):
    pass


class ProviderUnavailableError(AppError):
    """An external AI provider (LLM or embeddings) couldn't serve the request:
    rate limit, outage, timeout, or a malformed response. Temporary by nature."""
