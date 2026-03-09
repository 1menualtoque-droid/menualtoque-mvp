# app/frameworks/http/routes/users.py
import textwrap

from fastapi import APIRouter, Depends, HTTPException

from app.frameworks.http.deps import get_current_user_id, get_uow
from app.frameworks.http.schemas import (
    UpdateUserProfileIn,
    UserOut,
)
from app.use_cases.ports import UnitOfWork
from app.use_cases.user.get_user_profile import GetUserProfile
from app.use_cases.user.update_user_profile import UpdateUserProfile

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


def user_to_user_out(user) -> UserOut:
    """Convert User entity to UserOut schema."""
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        picture_url=user.picture_url,
        email_verified=user.email_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
    description=textwrap.dedent(
        """
        Fetch the authenticated user's full profile including role information.
        
        Returns complete user information including their role (client/restaurant).
        """
    ),
    responses={
        200: {"model": UserOut, "description": "User profile retrieved successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get the current authenticated user's profile."""
    use_case = GetUserProfile(uow)
    user = await use_case.execute(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_user_out(user)


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Update user profile",
    description=textwrap.dedent(
        """
        Partially update user profile fields.
        
        Only send the fields you want to update. Other fields remain unchanged.
        
        **Allowed fields:**
        - full_name
        
        **NOT allowed:**
        - email (requires re-verification)
        - password (use /auth/change-password)
        """
    ),
    responses={
        200: {"model": UserOut, "description": "Profile updated successfully"},
        400: {"description": "Invalid update request"},
        422: {"description": "Validation errors"},
    },
)
async def update_profile(
    updates: UpdateUserProfileIn,
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    """Update the authenticated user's profile."""
    use_case = UpdateUserProfile(uow)
    try:
        user = await use_case.execute(
            user_id=current_user_id,
            full_name=updates.full_name,
        )
        return user_to_user_out(user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
