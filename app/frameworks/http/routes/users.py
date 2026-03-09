# app/frameworks/http/routes/users.py
import textwrap
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.frameworks.http.deps import get_current_user_id, get_uow
from app.frameworks.http.schemas import (
    ApiResponse,
    CompleteOnboardingIn,
    MessageResponse,
    OnboardingData,
    UpdateUserProfileIn,
    UserOut,
)
from app.use_cases.ports import UnitOfWork
from app.use_cases.user.complete_onboarding import CompleteOnboarding
from app.use_cases.user.delete_user import DeleteUser
from app.use_cases.user.get_onboarding import GetOnboarding
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
    onboarding_data = None
    if user.onboarding_completed:
        onboarding_data = OnboardingData(
            needs_nutritional_plan=user.needs_nutritional_plan,
            sex=user.sex,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            activity_level=user.activity_level,
            sport=user.sport,
            goals=user.goals or [],
            available_foods=user.available_foods or [],
            target_calories=user.target_calories,
            completed_at=user.onboarding_completed_at,
        )
    
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        picture_url=user.picture_url,
        email_verified=user.email_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        onboarding_completed=user.onboarding_completed,
        onboarding=onboarding_data,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
    description=textwrap.dedent(
        """
        Fetch the authenticated user's full profile including onboarding data.
        
        Returns complete user information with onboarding data if completed.
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


@router.post(
    "/me/onboarding",
    summary="Complete onboarding",
    description=textwrap.dedent(
        """
        Submit onboarding data after completing the 5-step wizard.
        
        Calculates target calories using the Harris-Benedict formula based on:
        - Sex, weight, height
        - Activity level
        
        Sets onboarding_completed to true and marks completion timestamp.
        """
    ),
    responses={
        200: {"description": "Onboarding completed successfully"},
        400: {"description": "Onboarding already completed"},
        422: {"description": "Validation errors"},
    },
)
async def complete_onboarding(
    data: CompleteOnboardingIn,
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    """Complete user onboarding."""
    use_case = CompleteOnboarding(uow)
    try:
        result = await use_case.execute(
            user_id=current_user_id,
            needs_nutritional_plan=data.needs_nutritional_plan,
            sex=data.sex,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            activity_level=data.activity_level,
            sport=data.sport,
            goals=data.goals,
            available_foods=data.available_foods,
        )
        return ApiResponse.create_success(result)
    except ValueError as e:
        if "already completed" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


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
        - weight_kg (recalculates target_calories)
        - height_cm (recalculates target_calories)
        - activity_level (recalculates target_calories)
        - sport
        - goals
        - available_foods
        
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
            weight_kg=updates.weight_kg,
            height_cm=updates.height_cm,
            activity_level=updates.activity_level,
            sport=updates.sport,
            goals=updates.goals,
            available_foods=updates.available_foods,
        )
        return user_to_user_out(user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/me/onboarding",
    summary="Get onboarding data",
    description=textwrap.dedent(
        """
        Retrieve saved onboarding data.
        
        Useful for resuming incomplete onboarding or viewing current settings.
        """
    ),
    responses={
        200: {"description": "Onboarding data retrieved"},
        404: {"description": "No onboarding data found"},
    },
)
async def get_onboarding_data(
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get the authenticated user's onboarding data."""
    use_case = GetOnboarding(uow)
    try:
        data = await use_case.execute(current_user_id)
        if data is None:
            raise HTTPException(status_code=404, detail="No onboarding data found")
        return ApiResponse.create_success(data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description=textwrap.dedent(
        """
        Permanently delete the authenticated user's account.
        
        **WARNING:** This action:
        - Hard deletes the user account
        - Removes all related data (consumptions, summaries, tokens)
        - Cannot be undone
        """
    ),
    responses={
        204: {"description": "Account deleted successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def delete_account(
    current_user_id: int = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    """Delete the authenticated user's account."""
    use_case = DeleteUser(uow)
    try:
        await use_case.execute(current_user_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
