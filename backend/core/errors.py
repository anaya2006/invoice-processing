# backend/core/errors.py
"""Domain‑specific exception hierarchy for the invoice‑processing service.
Each exception corresponds to a distinct failure mode that the API can
return a structured error for (code/message)."""

class ServiceError(RuntimeError):
    """Base class for all service‑level errors."""
    status_code: int = 500
    error_code: str = "UNKNOWN"
    detail: str = "An unknown error occurred."

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)

    def as_dict(self) -> dict:
        return {"error": {"code": self.error_code, "message": self.detail}}

# Specific errors matching the SPEC error handling semantics
class BadRequestError(ServiceError):
    status_code = 400
    error_code = "BAD_REQUEST"

class UnauthorizedError(ServiceError):
    status_code = 401
    error_code = "UNAUTHORIZED"

class ForbiddenError(ServiceError):
    status_code = 403
    error_code = "FORBIDDEN"

class ConflictError(ServiceError):
    status_code = 409
    error_code = "CONFLICT"

class NotFoundError(ServiceError):
    status_code = 404
    error_code = "NOT_FOUND"

class ValidationError(ServiceError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
