from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserRoleEnum(str, PyEnum):
    CLIENT = "client"
    RESTAURANT = "restaurant"


UserRole = SAEnum(
    UserRoleEnum, name="user_role_enum", values_callable=lambda e: [m.value for m in e]
)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    role = Column(UserRole, nullable=False, default=UserRoleEnum.CLIENT)
    picture_url = Column(String(512), nullable=True)
    google_sub = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti = Column(String(64), unique=True, index=True)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EmailTokenModel(Base):
    __tablename__ = "email_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token = Column(String(128), unique=True, index=True)
    purpose = Column(String(32))  # confirm_email | reset_password
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
