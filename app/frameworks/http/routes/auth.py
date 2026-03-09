import textwrap

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.domain.errors import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    GoogleTokenVerificationError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.frameworks.http.deps import (
    get_current_user_id,
    get_google_verifier,
    get_hasher,
    get_jwt,
    get_mail,
    get_uow,
    settings,
)
from app.frameworks.http.rate_limiter import (
    RATE_LIMITS,
    rate_limit_auth,
)
from app.frameworks.http.schemas import (
    ApiResponse,
    ChangePasswordIn,
    ConfirmEmailIn,
    GoogleSignInIn,
    LoginIn,
    MessageResponse,
    RefreshOut,
    RegisterIn,
    RequestPasswordResetIn,
    ResetPasswordIn,
    Token,
)
from app.use_cases.auth.change_password import ChangePassword
from app.use_cases.auth.confirm_email import ConfirmEmail
from app.use_cases.auth.google_sign_in import GoogleSignIn
from app.use_cases.auth.login_password import LoginPassword
from app.use_cases.auth.logout import Logout, LogoutAll
from app.use_cases.auth.refresh_access import RefreshAccess
from app.use_cases.auth.register_user import RegisterUser
from app.use_cases.auth.request_password_reset import RequestPasswordReset
from app.use_cases.auth.reset_password import ResetPassword
from app.use_cases.ports import (
    EmailSender,
    GoogleTokenVerifier,
    JWTService,
    PasswordHasher,
    UnitOfWork,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)

# Common response models
responses = {
    200: {"model": Token, "description": "Successful Response"},
    400: {"model": MessageResponse, "description": "Bad Request"},
    401: {"model": MessageResponse, "description": "Unauthorized"},
    403: {"model": MessageResponse, "description": "Forbidden"},
    422: {"model": MessageResponse, "description": "Validation Error"},
}

SECURE_COOKIE = True  # set False for localhost HTTP if needed
COOKIE_KW = dict(httponly=True, secure=SECURE_COOKIE, samesite="lax")


def set_tokens(resp: Response, access: str, refresh: str):
    resp.set_cookie("access_token", access, **COOKIE_KW, max_age=60 * 15, path="/")
    resp.set_cookie(
        "refresh_token", refresh, **COOKIE_KW, max_age=60 * 60 * 24 * 30, path="/"
    )


@router.post(
    "/register",
    response_model=ApiResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=textwrap.dedent(
        """
        Register a new user with email and password.
        - **email**: Must be a valid email address
        - **password**: Must be at least 8 characters long
        - **first_name**: User's first name
        - **last_name**: User's last name
        Returns a success message if registration is successful.
        """
    ),
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Email already registered"},
        429: {"description": "Rate limit exceeded"},
    },
)
@rate_limit_auth(RATE_LIMITS["auth"]["register"])
async def register(
    request: Request,
    response: Response,
    payload: RegisterIn,
    uow: UnitOfWork = Depends(get_uow),
    hasher: PasswordHasher = Depends(get_hasher),
    mail: EmailSender = Depends(get_mail),
):
    try:
        uc = RegisterUser(uow, hasher, mail, settings.APP_URL)
        await uc.execute(
            payload.email, payload.full_name, payload.password, payload.role
        )
        return ApiResponse.create_success(
            data=MessageResponse(message="Revisa tu email para confirmar la cuenta")
        )
    except EmailAlreadyExistsError:
        raise  # Will be handled by domain_error_handler


@router.post(
    "/login/password",
    response_model=ApiResponse[Token],
    summary="Login with email and password",
    description=textwrap.dedent(
        """
        Authenticate a user with email and password.

        - **email**: Registered email address
        - **password**: Account password

        Returns access and refresh tokens on successful authentication.
        The refresh token is set as an HTTP-only cookie.
        """
    ),
    responses=responses,
)
@rate_limit_auth(RATE_LIMITS["auth"]["login"])
async def login_password(
    request: Request,
    response: Response,
    data: LoginIn,
    uow: UnitOfWork = Depends(get_uow),
    hasher: PasswordHasher = Depends(get_hasher),
    jwt: JWTService = Depends(get_jwt),
):
    try:
        result = await LoginPassword(uow, hasher, jwt).execute(
            data.email, data.password
        )
        user, access, refresh = result["user"], result["access"], result["refresh"]
        set_tokens(response, access, refresh)
        return ApiResponse.create_success(
            data=Token(access_token=access, refresh_token=refresh)
        )
    except (InvalidCredentialsError, EmailNotVerifiedError):
        raise  # Will be handled by domain_error_handler


@router.post(
    "/token",
    response_model=ApiResponse[Token],
    include_in_schema=False,
    summary="OAuth2 compatible token login",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    uow: UnitOfWork = Depends(get_uow),
    hasher: PasswordHasher = Depends(get_hasher),
    jwt: JWTService = Depends(get_jwt),
):
    """OAuth2 compatible token login, get an access token for future requests"""
    return await login_password(
        response=Response(),
        data=LoginIn(email=form_data.username, password=form_data.password),
        uow=uow,
        hasher=hasher,
        jwt=jwt,
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshOut],
    summary="Refresh access token",
    description=textwrap.dedent(
        """
        Get a new access token using a refresh token.
        The refresh token should be provided as an HTTP-only cookie.
        Returns a new access token and refresh token.
        """
    ),
    responses=responses,
)
@rate_limit_auth(RATE_LIMITS["auth"]["refresh"])
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    uow: UnitOfWork = Depends(get_uow),
    jwt: JWTService = Depends(get_jwt),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Falta refresh token")

    try:
        access = await RefreshAccess(uow, jwt).execute(refresh_token)
        # update access cookie only (keep refresh as-is)
        response.set_cookie(
            "access_token", access, **COOKIE_KW, max_age=60 * 15, path="/"
        )
        return ApiResponse.create_success(data=RefreshOut(access_token=access))
    except InvalidTokenError:
        raise  # Will be handled by domain_error_handler


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description=textwrap.dedent(
        """
        Logout the current user by revoking the refresh token.

        The refresh token is expected in an HTTP-only cookie.
        Clears the refresh token cookie.
        """
    ),
    responses={
        204: {"description": "Successfully logged out"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    response: Response,
    current_user_id: int = Depends(get_current_user_id),
    refresh_token: str | None = Cookie(default=None),
    uow: UnitOfWork = Depends(get_uow),
    jwt: JWTService = Depends(get_jwt),
):
    if refresh_token:
        try:
            await Logout(uow, jwt).execute(refresh_token)
        except InvalidTokenError:
            pass  # ignore to avoid leaking details

    # clear cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/logout/all",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[MessageResponse],
    summary="Logout from all devices",
    description=textwrap.dedent(
        """
        Logout the user from all devices by revoking all refresh tokens.

        Requires a valid access token in the Authorization header.
        """
    ),
    responses={
        200: {"model": MessageResponse, "description": "Logged out from all devices"},
        401: {"description": "Not authenticated"},
    },
)
async def logout_all(
    response: Response,
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    await LogoutAll(uow).execute(current_user_id)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return ApiResponse.create_success(
        data=MessageResponse(message="Sesiones cerradas en todos los dispositivos")
    )


@router.post(
    "/confirm-email",
    response_model=ApiResponse[MessageResponse],
    summary="Confirm email",
    description=textwrap.dedent(
        """
        Confirm the user's email address.

        - **token**: Email confirmation token

        Returns a success message if the email is confirmed.
        """
    ),
    responses={
        200: {"model": MessageResponse, "description": "Email confirmed"},
        400: {"model": MessageResponse, "description": "Invalid token"},
    },
)
async def confirm_email(data: ConfirmEmailIn, uow: UnitOfWork = Depends(get_uow)):
    try:
        await ConfirmEmail(uow).execute(data.token)
        return ApiResponse.create_success(
            data=MessageResponse(message="Correo confirmado")
        )
    except InvalidTokenError:
        raise  # Will be handled by domain_error_handler


@router.post(
    "/request-password-reset",
    response_model=ApiResponse[MessageResponse],
    summary="Request password reset",
    description=textwrap.dedent(
        """
        Request a password reset for the user.

        - **email**: User's email address

        Returns a success message if the request is successful.
        """
    ),
    responses={
        200: {"model": MessageResponse, "description": "Password reset requested"},
        400: {"model": MessageResponse, "description": "Invalid email"},
        429: {"description": "Rate limit exceeded"},
    },
)
@rate_limit_auth(RATE_LIMITS["auth"]["password_reset"])
async def request_reset(
    request: Request,
    response: Response,
    data: RequestPasswordResetIn,
    uow: UnitOfWork = Depends(get_uow),
    mail: EmailSender = Depends(get_mail),
):
    await RequestPasswordReset(uow, mail, settings.APP_URL).execute(data.email)
    # Always OK to avoid user enumeration
    return ApiResponse.create_success(
        data=MessageResponse(message="Si el email existe, enviaremos instrucciones")
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[MessageResponse],
    summary="Reset password",
    description=textwrap.dedent(
        """
        Reset the user's password.
        - **token**: Password reset token
        - **new_password**: New password
        Returns a success message if the password is reset.
        """
    ),
    responses={
        200: {"model": MessageResponse, "description": "Password reset"},
        400: {"model": MessageResponse, "description": "Invalid token or password"},
        429: {"description": "Rate limit exceeded"},
    },
)
@rate_limit_auth(RATE_LIMITS["auth"]["default"])
async def reset_password(
    request: Request,
    response: Response,
    data: ResetPasswordIn,
    uow: UnitOfWork = Depends(get_uow),
    hasher: PasswordHasher = Depends(get_hasher),
    mail: EmailSender = Depends(get_mail),
):
    try:
        await ResetPassword(uow, hasher, mail).execute(data.token, data.new_password)
        return ApiResponse.create_success(
            data=MessageResponse(message="Contraseña actualizada")
        )
    except InvalidTokenError:
        raise  # Will be handled by domain_error_handler


@router.post("/change-password", response_model=ApiResponse[MessageResponse])
async def change_password(
    response: Response,
    data: ChangePasswordIn,
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
    hasher: PasswordHasher = Depends(get_hasher),
    mail: EmailSender = Depends(get_mail),
):
    try:
        await ChangePassword(uow, hasher, mail).execute(
            current_user_id, data.current_password, data.new_password
        )
        return ApiResponse.create_success(
            data=MessageResponse(message="Contraseña cambiada")
        )
    except (InvalidCredentialsError, InvalidTokenError):
        raise  # Will be handled by domain_error_handler


@router.post("/google", response_model=ApiResponse[Token])
async def google_sign_in(
    response: Response,
    data: GoogleSignInIn,
    uow: UnitOfWork = Depends(get_uow),
    gv: GoogleTokenVerifier = Depends(get_google_verifier),
    jwt: JWTService = Depends(get_jwt),
):
    try:
        uc = GoogleSignIn(uow, gv, jwt)
        user, access, refresh = await uc.execute(data.id_token)
        set_tokens(response, access, refresh)
        return ApiResponse.create_success(
            data=Token(access_token=access, refresh_token=refresh)
        )
    except GoogleTokenVerificationError:
        raise  # Will be handled by domain_error_handler
