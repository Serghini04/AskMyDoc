"""Maps domain exceptions to HTTP responses — the only place that knows both."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    AppError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    PayloadTooLargeError,
    ProviderUnavailableError,
    UnsupportedMediaTypeError,
)

logger = logging.getLogger(__name__)

STATUS_CODES: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidRequestError: status.HTTP_400_BAD_REQUEST,
    UnsupportedMediaTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    PayloadTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
}

PROVIDER_UNAVAILABLE_DETAIL = "The AI model is busy right now. Please try again in a few seconds."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable(request: Request, exc: ProviderUnavailableError) -> JSONResponse:
        # Provider details can include request metadata: log them, don't return them.
        logger.warning(
            "AI provider unavailable on %s %s: %s", request.method, request.url.path, exc
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": PROVIDER_UNAVAILABLE_DETAIL},
        )

    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        status_code = next(
            (code for cls, code in STATUS_CODES.items() if isinstance(exc, cls)),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return JSONResponse(status_code=status_code, content={"detail": exc.detail})
