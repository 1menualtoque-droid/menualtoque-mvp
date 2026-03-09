"""Domain-specific exceptions for the Fitsuyo application.
These exceptions represent business rule violations and domain constraints.
"""


class DomainError(Exception):
    """Base exception for all domain-related errors"""

    pass


class UserNotFoundError(DomainError):
    """Raised when a user cannot be found"""

    pass


class InvalidCredentialsError(DomainError):
    """Raised when authentication credentials are invalid"""

    pass


class EmailAlreadyExistsError(DomainError):
    """Raised when trying to register with an existing email"""

    pass


class EmailNotVerifiedError(DomainError):
    """Raised when trying to access features requiring email verification"""

    pass


class InvalidTokenError(DomainError):
    """Raised when a token is invalid, expired, or already used"""

    pass


class PasswordTooWeakError(DomainError):
    """Raised when password doesn't meet security requirements"""

    pass


class GoogleTokenVerificationError(DomainError):
    """Raised when Google token verification fails"""

    pass


class RefreshTokenExpiredError(DomainError):
    """Raised when refresh token has expired"""

    pass


class RefreshTokenRevokedError(DomainError):
    """Raised when refresh token has been revoked"""

    pass


class SamePasswordError(DomainError):
    """Raised when new password is the same as the current password"""

    pass
