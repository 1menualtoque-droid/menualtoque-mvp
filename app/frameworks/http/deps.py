from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.frameworks.settings import Settings
from app.use_cases.nutrition.calculate_nutrition import NutritionCalculator
from app.interfaces.persistence.uow import SQLAlchemyUnitOfWork
from app.interfaces.providers.email_sender import EmailSenderImpl
from app.interfaces.providers.google_verifier import GoogleVerifierImpl
from app.interfaces.security.jwt_service import JWTServiceImpl
from app.interfaces.security.password_hasher import PasswordHasherImpl
from app.use_cases.ports import JWTService

settings = Settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

security = HTTPBearer()


def get_uow():
    return SQLAlchemyUnitOfWork(SessionLocal)


def get_jwt():
    return JWTServiceImpl(settings)


def get_hasher():
    return PasswordHasherImpl()


def get_google_verifier():
    return GoogleVerifierImpl(settings.GOOGLE_CLIENT_ID)


def get_mail():
    return EmailSenderImpl(settings)


def get_calculator(uow=Depends(get_uow)):
    return NutritionCalculator(uow)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt: JWTService = Depends(get_jwt),
) -> int:
    """Extract and validate user ID from JWT access token"""
    try:
        token = credentials.credentials
        payload = jwt.parse_access(token)
        user_id = int(payload.get("sub"))
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "bearer"},
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    uow = Depends(get_uow),
) -> dict:
    """Get the current authenticated user"""
    async with uow:
        user = await uow.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user credentials",
                headers={"WWW-Authenticate": "bearer"},
            )
        
        # Return minimal user info for admin/authorization checks
        return {
            "id": user.id,
            "email": str(user.email),
            "role": "admin"  # Placeholder: implement actual role management
        }
