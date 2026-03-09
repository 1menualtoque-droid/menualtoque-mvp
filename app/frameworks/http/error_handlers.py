"""HTTP error handlers for mapping domain exceptions to appropriate HTTP responses."""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import ValidationError

from app.frameworks.http.schemas import ApiResponse
from app.domain.errors import DomainError


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    print('domain_error_handler>', exc)
    error_mapping = {
        "UserNotFoundError": (404, "User not found"),
        "EmailAlreadyExistsError": (409, "Email already registered"),
        "InvalidCredentialsError": (401, "Invalid credentials"),
        "EmailNotVerifiedError": (403, "Email not verified"),
        "InvalidTokenError": (400, "Invalid or expired token"),
        "PasswordTooWeakError": (400, "Password does not meet requirements"),
        "GoogleTokenVerificationError": (401, "Google token verification failed"),
        "RefreshTokenExpiredError": (401, "Refresh token expired"),
        "RefreshTokenRevokedError": (401, "Refresh token revoked"),
        "SamePasswordError": (400, "New password cannot be the same as current password"),
    }
    
    error_type = exc.__class__.__name__
    print('error_type>', error_type)
    status_code, message = error_mapping.get(error_type, (400, str(exc)))
    print('status_code>', status_code)
    print('message>', message)
    response = ApiResponse.create_error(
        code=error_type,
        message=message,
        status_code=status_code
    )
    print('response>', response)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json")
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field = ".".join(map(str, error["loc"]))
        errors.append({
            "code": error["type"],
            "message": error["msg"],
            "target": field
        })
    
    response = ApiResponse.create_error(
        code="ValidationError",
        message="One or more validation errors occurred",
        details={"errors": errors}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(mode="json")
    )


async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    response = ApiResponse.create_error(
        code="InternalServerError",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json")
    )
