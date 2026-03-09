# app/interfaces/persistence/repositories.py
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.food import Food
from app.domain.entities.user import User
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.email_tokens import EmailToken
from app.domain.entities.consumption import Consumption, ConsumptionItem
from datetime import date
from app.interfaces.persistence.models import (
    EmailTokenModel,
    RefreshTokenModel,
    UserModel,
    Foods,
    FoodPortions,
    FoodAliases,
    FoodVersions,
    UserConsumptions,
    ConsumptionItems,
    DailySummaries,
)

# ---------------------------------------------------------------------------
# Helpers: map Domain <-> ORM safely (supports Value Objects with `.value`)
# ---------------------------------------------------------------------------


def _val(x: Any) -> Any:
    """Return VO.value if present, else the primitive itself."""
    return getattr(x, "value", x)


def _food_from_model(m: Foods) -> Food:
    return Food.from_model(m)


def _food_to_values(f: Food) -> dict[str, Any]:
    return f.to_model_data()


def _user_from_model(m: UserModel) -> User:
    return User.from_model(m)


def _consumption_from_model(m: UserConsumptions) -> Consumption:
    """Convert SQLAlchemy model to Consumption domain entity."""
    return Consumption(
        id=m.id,
        user_id=m.user_id,
        occurred_at=m.occurred_at,
        local_date=m.local_date,
        meal=m.meal.value if m.meal else "",
        note=m.note,
        total_kcal=m.total_kcal,
        total_carbs_g=float(m.total_carbs_g or 0),
        total_protein_g=float(m.total_protein_g or 0),
        total_fat_g=float(m.total_fat_g or 0),
        total_fiber_g=float(m.total_fiber_g or 0),
        total_sodium_mg=int(m.total_sodium_mg or 0),
        items=[],  # Populated separately if needed
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _consumption_to_values(c: Consumption) -> dict[str, Any]:
    """Convert Consumption domain entity to SQLAlchemy model data."""
    # Convert timezone-aware datetimes to timezone-naive for PostgreSQL
    occurred_at = c.occurred_at.replace(tzinfo=None) if c.occurred_at and c.occurred_at.tzinfo else c.occurred_at
    created_at = c.created_at.replace(tzinfo=None) if c.created_at and c.created_at.tzinfo else c.created_at
    updated_at = c.updated_at.replace(tzinfo=None) if c.updated_at and c.updated_at.tzinfo else c.updated_at
    
    return {
        "user_id": c.user_id,
        "occurred_at": occurred_at,
        "local_date": c.local_date,
        "meal": c.meal,
        "note": c.note,
        "total_kcal": c.total_kcal,
        "total_carbs_g": c.total_carbs_g,
        "total_protein_g": c.total_protein_g,
        "total_fat_g": c.total_fat_g,
        "total_fiber_g": c.total_fiber_g,
        "total_sodium_mg": c.total_sodium_mg,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _consumption_item_from_model(m: ConsumptionItems) -> ConsumptionItem:
    """Convert SQLAlchemy model to ConsumptionItem domain entity."""
    return ConsumptionItem(
        id=m.id,
        consumption_id=m.consumption_id,
        food_id=m.food_id,
        custom_food_id=m.custom_food_id,
        original_name=m.original_name,
        quantity=float(m.quantity or 0),
        unit=m.unit.value if m.unit else "",
        portion_id=m.portion_id,
        original_portion_label=m.original_portion_label,
        grams=float(m.grams or 0) if m.grams else None,
        ml=float(m.ml or 0) if m.ml else None,
        using_food_version=m.using_food_version,
        kcal=m.kcal,
        carbs_g=float(m.carbs_g or 0),
        protein_g=float(m.protein_g or 0),
        fat_g=float(m.fat_g or 0),
        fiber_g=float(m.fiber_g or 0),
        sodium_mg=int(m.sodium_mg or 0),
        position=m.position,
        created_at=m.created_at,
    )


def _consumption_item_to_values(ci: ConsumptionItem) -> dict[str, Any]:
    """Convert ConsumptionItem domain entity to SQLAlchemy model data."""
    return {
        "consumption_id": ci.consumption_id,
        "food_id": ci.food_id,
        "custom_food_id": ci.custom_food_id,
        "original_name": ci.original_name,
        "quantity": ci.quantity,
        "unit": ci.unit,
        "portion_id": ci.portion_id,
        "original_portion_label": ci.original_portion_label,
        "grams": ci.grams,
        "ml": ci.ml,
        "using_food_version": ci.using_food_version,
        "kcal": ci.kcal,
        "carbs_g": ci.carbs_g,
        "protein_g": ci.protein_g,
        "fat_g": ci.fat_g,
        "fiber_g": ci.fiber_g,
        "sodium_mg": ci.sodium_mg,
        "position": ci.position,
        "created_at": ci.created_at,
    }


def _user_to_values(u: User) -> dict[str, Any]:
    return {
        "email": _val(u.email),
        "full_name": _val(u.full_name),
        "picture_url": u.picture_url,
        "google_sub": u.google_sub,
        "password_hash": _val(u.password_hash) if u.password_hash else None,
        "email_verified": u.email_verified,
        "last_login_at": u.last_login_at,
        "onboarding_completed": u.onboarding_completed,
        "onboarding_completed_at": u.onboarding_completed_at,
        "needs_nutritional_plan": u.needs_nutritional_plan,
        "sex": u.sex,
        "height_cm": u.height_cm,
        "weight_kg": u.weight_kg,
        "activity_level": u.activity_level,
        "sport": u.sport,
        "goals": u.goals,
        "available_foods": u.available_foods,
        "target_calories": u.target_calories,
        # updated_at set on UPDATE using DB clock below
    }


def _rt_from_model(m: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=m.id,
        user_id=m.user_id,
        jti=m.jti,
        revoked=m.revoked,
        expires_at=m.expires_at,
        created_at=m.created_at,
    )


def _rt_to_values(rt: RefreshToken) -> dict[str, Any]:
    return {
        "user_id": rt.user_id,
        "jti": rt.jti,
        "revoked": rt.revoked,
        "expires_at": rt.expires_at,
    }


def _et_from_model(m: EmailTokenModel) -> EmailToken:
    return EmailToken(
        id=m.id,
        user_id=m.user_id,
        token=m.token,
        purpose=m.purpose,
        used=m.used,
        expires_at=m.expires_at,
        created_at=m.created_at,
    )


def _et_to_values(et: EmailToken) -> dict[str, Any]:
    return {
        "user_id": et.user_id,
        "token": et.token,
        "purpose": et.purpose,
        "used": et.used,
        "expires_at": et.expires_at,
    }


# ---------------------------------------------------------------------------
# User Repository (implements UserRepo port)
# ---------------------------------------------------------------------------


class SQLUserRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def get_by_email(self, email: str) -> User | None:
        q = select(UserModel).where(UserModel.email == email.lower().strip())
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def get_by_google_sub(self, sub: str) -> User | None:
        q = select(UserModel).where(UserModel.google_sub == sub)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def get_by_id(self, user_id: int) -> User | None:
        q = select(UserModel).where(UserModel.id == user_id)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def add(self, user: User) -> User:
        m = UserModel(**_user_to_values(user))
        self.s.add(m)
        await self.s.flush()  # assigns PK
        await self.s.refresh(m)
        user.id = m.id
        user.created_at = m.created_at
        user.updated_at = m.updated_at
        return user

    async def update(self, user: User) -> None:
        values = _user_to_values(user)
        # let DB set updated_at = now()
        values["updated_at"] = func.now()
        await self.s.execute(update(UserModel).where(UserModel.id == user.id).values(**values))

    async def delete(self, user_id: int) -> None:
        """Hard delete user and all related data (cascades via FK constraints)."""
        await self.s.execute(delete(UserModel).where(UserModel.id == user_id))


# ---------------------------------------------------------------------------
# Refresh Token Repository (implements RefreshTokenRepo port)
# ---------------------------------------------------------------------------


class SQLRefreshTokenRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, rt: RefreshToken) -> RefreshToken:
        m = RefreshTokenModel(**_rt_to_values(rt))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        rt.id = m.id
        return rt

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        q = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _rt_from_model(m) if m else None

    async def mark_revoked(self, jti: str) -> None:
        await self.s.execute(
            update(RefreshTokenModel).where(RefreshTokenModel.jti == jti).values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: int) -> int:
        res = await self.s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        # SQLAlchemy 2.x returns CursorResult; rowcount may be -1 for some drivers.
        return getattr(res, "rowcount", 0) or 0


# ---------------------------------------------------------------------------
# Email Token Repository (implements EmailTokenRepo port)
# ---------------------------------------------------------------------------


class SQLEmailTokenRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, et: EmailToken) -> EmailToken:
        m = EmailTokenModel(**_et_to_values(et))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        et.id = m.id
        return et

    async def get_valid(self, token: str, purpose: str) -> EmailToken | None:
        q = select(EmailTokenModel).where(
            and_(
                EmailTokenModel.token == token,
                EmailTokenModel.purpose == purpose,
                EmailTokenModel.used.is_(False),
                EmailTokenModel.expires_at > func.now(),
            )
        )
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _et_from_model(m) if m else None

    async def mark_used(self, email_token_id: int) -> None:
        await self.s.execute(
            update(EmailTokenModel).where(EmailTokenModel.id == email_token_id).values(used=True)
        )


class SQLFoodRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def _load_portions(self, food_id: int) -> list[dict]:
        """Load portions for a food."""
        q = select(FoodPortions).where(FoodPortions.food_id == food_id)
        r = await self.s.execute(q)
        portions = r.scalars().all()
        return [
            {
                "id": p.id,
                "label": p.label,
                "grams_equivalent": float(p.grams_equivalent) if p.grams_equivalent else None,
                "ml_equivalent": float(p.ml_equivalent) if p.ml_equivalent else None,
                "is_default": p.is_default,
                "created_at": p.created_at.isoformat(),
            }
            for p in portions
        ]

    async def _load_aliases(self, food_id: int) -> list[str]:
        """Load aliases for a food."""
        q = select(FoodAliases).where(FoodAliases.food_id == food_id)
        r = await self.s.execute(q)
        aliases = r.scalars().all()
        return [a.alias for a in aliases]

    async def _save_portions(self, food_id: int, portions: list[dict]) -> None:
        """Save or update portions for a food."""
        # Delete existing portions
        await self.s.execute(delete(FoodPortions).where(FoodPortions.food_id == food_id))
        
        # Add new portions
        if portions:
            for portion in portions:
                portion_model = FoodPortions(
                    food_id=food_id,
                    label=portion.get("label", ""),
                    grams_equivalent=portion.get("grams_equivalent"),
                    ml_equivalent=portion.get("ml_equivalent"),
                    is_default=portion.get("is_default", False),
                )
                self.s.add(portion_model)

    async def _save_aliases(self, food_id: int, aliases: list[str]) -> None:
        """Save or update aliases for a food."""
        # Delete existing aliases
        await self.s.execute(delete(FoodAliases).where(FoodAliases.food_id == food_id))
        
        # Add new aliases
        if aliases:
            for alias in aliases:
                alias_model = FoodAliases(
                    food_id=food_id,
                    alias=alias,
                )
                self.s.add(alias_model)

    async def search(self, query: str | None, page: int, per_page: int) -> list[Food]:
        q = select(Foods).where(Foods.is_deleted == False)
        if query:
            q = q.where(Foods.name.ilike(f'%{query}%'))
        q = q.offset((page - 1) * per_page).limit(per_page)
        r = await self.s.execute(q)
        models = r.scalars().all()
        foods = []
        for model in models:
            food = _food_from_model(model)
            food.portions = await self._load_portions(model.id)
            food.aliases = await self._load_aliases(model.id)
            foods.append(food)
        return foods

    async def get_by_id(self, food_id: int) -> Food | None:
        q = select(Foods).where(Foods.id == food_id, Foods.is_deleted == False)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        if not m:
            return None
        food = _food_from_model(m)
        food.portions = await self._load_portions(m.id)
        food.aliases = await self._load_aliases(m.id)
        return food

    async def add(self, food: Food) -> Food:
        values = _food_to_values(food)
        # Remove id from values if present (will be auto-generated)
        values.pop("id", None)
        m = Foods(**values)
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        # Update the food entity with the auto-generated ID
        food.id = m.id
        food.created_at = m.created_at
        food.updated_at = m.updated_at
        
        # Save portions and aliases if provided
        portions = food.portions if hasattr(food, 'portions') and food.portions else []
        aliases = food.aliases if hasattr(food, 'aliases') and food.aliases else []
        
        if portions:
            await self._save_portions(food.id, portions)
        if aliases:
            await self._save_aliases(food.id, aliases)

        # Reload portions and aliases
        food.portions = await self._load_portions(food.id)
        food.aliases = await self._load_aliases(food.id)
        
        return food

    async def update(self, food: Food) -> None:
        values = _food_to_values(food)
        # Remove fields that shouldn't be updated
        values.pop("id", None)  # Never update the ID
        values.pop("created_at", None)  # Never update created_at
        values.pop("created_by", None)  # Never update created_by (preserve original creator)
        values["updated_at"] = func.now()
        await self.s.execute(update(Foods).where(Foods.id == food.id).values(**values))
        
        # Update portions and aliases if provided
        if hasattr(food, 'portions') and food.portions is not None:
            await self._save_portions(food.id, food.portions)
        if hasattr(food, 'aliases') and food.aliases is not None:
            await self._save_aliases(food.id, food.aliases)

    async def delete(self, food_id: int) -> None:
        await self.s.execute(update(Foods).where(Foods.id == food_id).values(is_deleted=True))

    async def add_portion(self, food_id: int, portion: dict) -> dict:
        """Add a portion to a food."""
        portion_model = FoodPortions(
            food_id=food_id,
            label=portion.get("label", ""),
            grams_equivalent=portion.get("grams_equivalent"),
            ml_equivalent=portion.get("ml_equivalent"),
            is_default=portion.get("is_default", False),
        )
        self.s.add(portion_model)
        await self.s.flush()
        await self.s.refresh(portion_model)
        return {
            "id": portion_model.id,
            "food_id": portion_model.food_id,
            "label": portion_model.label,
            "grams_equivalent": float(portion_model.grams_equivalent) if portion_model.grams_equivalent else None,
            "ml_equivalent": float(portion_model.ml_equivalent) if portion_model.ml_equivalent else None,
            "is_default": portion_model.is_default,
            "created_at": portion_model.created_at.isoformat(),
        }

    async def update_portion(self, portion_id: int, portion: dict) -> dict:
        """Update a portion."""
        values = {}
        if "label" in portion:
            values["label"] = portion["label"]
        if "grams_equivalent" in portion:
            values["grams_equivalent"] = portion["grams_equivalent"]
        if "ml_equivalent" in portion:
            values["ml_equivalent"] = portion["ml_equivalent"]
        if "is_default" in portion:
            values["is_default"] = portion["is_default"]
        
        await self.s.execute(
            update(FoodPortions).where(FoodPortions.id == portion_id).values(**values)
        )
        
        # Reload and return
        q = select(FoodPortions).where(FoodPortions.id == portion_id)
        r = await self.s.execute(q)
        m = r.scalar_one()
        return {
            "id": m.id,
            "food_id": m.food_id,
            "label": m.label,
            "grams_equivalent": float(m.grams_equivalent) if m.grams_equivalent else None,
            "ml_equivalent": float(m.ml_equivalent) if m.ml_equivalent else None,
            "is_default": m.is_default,
            "created_at": m.created_at.isoformat(),
        }

    async def delete_portion(self, portion_id: int) -> None:
        """Delete a portion."""
        await self.s.execute(delete(FoodPortions).where(FoodPortions.id == portion_id))

    async def add_alias(self, food_id: int, alias: str) -> dict:
        """Add an alias to a food."""
        alias_model = FoodAliases(
            food_id=food_id,
            alias=alias,
        )
        self.s.add(alias_model)
        await self.s.flush()
        await self.s.refresh(alias_model)
        return {
            "id": alias_model.id,
            "food_id": alias_model.food_id,
            "alias": alias_model.alias,
            "created_at": alias_model.created_at.isoformat(),
        }

    async def delete_alias(self, alias_id: int) -> None:
        """Delete an alias."""
        await self.s.execute(delete(FoodAliases).where(FoodAliases.id == alias_id))


class SQLFoodVersionRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def get_by_food(self, food_id: int) -> list[dict]:
        """Get all versions for a food."""
        q = select(FoodVersions).where(FoodVersions.food_id == food_id)
        q = q.order_by(FoodVersions.version.desc())
        r = await self.s.execute(q)
        versions = r.scalars().all()
        return [
            {
                "id": v.id,
                "food_id": v.food_id,
                "version": v.version,
                "snapshot": v.snapshot,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]

    async def get_by_food_and_version(self, food_id: int, version: int) -> dict | None:
        """Get a specific version of a food."""
        q = select(FoodVersions).where(
            and_(FoodVersions.food_id == food_id, FoodVersions.version == version)
        )
        r = await self.s.execute(q)
        v = r.scalar_one_or_none()
        if not v:
            return None
        return {
            "id": v.id,
            "food_id": v.food_id,
            "version": v.version,
            "snapshot": v.snapshot,
            "created_at": v.created_at.isoformat(),
        }


class SQLConsumptionRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, consumption: Consumption) -> Consumption:
        m = UserConsumptions(**_consumption_to_values(consumption))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        consumption.id = m.id
        consumption.created_at = m.created_at
        consumption.updated_at = m.updated_at
        return consumption

    async def get_by_id(self, consumption_id: int) -> Consumption | None:
        q = select(UserConsumptions).where(UserConsumptions.id == consumption_id)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        if not m:
            return None
        consumption = _consumption_from_model(m)
        # Load items
        consumption.items = await self._load_items(m.id)
        return consumption

    async def get_by_user_and_date(
        self, user_id: int, filter_date: str | None = None
    ) -> list[Consumption]:
        q = select(UserConsumptions).where(UserConsumptions.user_id == user_id)
        if filter_date:
            filter_date_obj = date.fromisoformat(filter_date)
            q = q.where(UserConsumptions.local_date == filter_date_obj)
        q = q.order_by(UserConsumptions.occurred_at.desc())
        r = await self.s.execute(q)
        models = r.scalars().all()
        consumptions = []
        for model in models:
            consumption = _consumption_from_model(model)
            consumption.items = await self._load_items(model.id)
            consumptions.append(consumption)
        return consumptions

    async def aggregate_daily_totals(self, user_id: int, target_date: date) -> dict | None:
        """Aggregate nutrition totals for a user on a specific date.
        
        Uses a single optimized SQL query with aggregation functions.
        """
        q = select(
            func.count(UserConsumptions.id).label('meals_count'),
            func.coalesce(func.sum(UserConsumptions.total_kcal), 0).label('total_kcal'),
            func.coalesce(func.sum(UserConsumptions.total_carbs_g), 0).label('total_carbs_g'),
            func.coalesce(func.sum(UserConsumptions.total_protein_g), 0).label('total_protein_g'),
            func.coalesce(func.sum(UserConsumptions.total_fat_g), 0).label('total_fat_g'),
            func.coalesce(func.sum(UserConsumptions.total_fiber_g), 0).label('total_fiber_g'),
            func.coalesce(func.sum(UserConsumptions.total_sodium_mg), 0).label('total_sodium_mg'),
        ).where(
            and_(
                UserConsumptions.user_id == user_id,
                UserConsumptions.local_date == target_date,
            )
        )
        r = await self.s.execute(q)
        row = r.one()
        
        if row.meals_count == 0:
            return None
        
        # Count items separately for efficiency
        items_q = select(func.count(ConsumptionItems.id)).select_from(
            ConsumptionItems
        ).join(
            UserConsumptions,
            ConsumptionItems.consumption_id == UserConsumptions.id
        ).where(
            and_(
                UserConsumptions.user_id == user_id,
                UserConsumptions.local_date == target_date,
            )
        )
        items_r = await self.s.execute(items_q)
        items_count = items_r.scalar() or 0
        
        total_kcal = int(row.total_kcal)
        total_carbs = float(row.total_carbs_g)
        total_protein = float(row.total_protein_g)
        total_fat = float(row.total_fat_g)
        
        # Calculate macro percentages
        pct_carbs = pct_protein = pct_fat = None
        if total_kcal > 0:
            pct_carbs = round((total_carbs * 4 / total_kcal) * 100, 2)
            pct_protein = round((total_protein * 4 / total_kcal) * 100, 2)
            pct_fat = round((total_fat * 9 / total_kcal) * 100, 2)
        
        return {
            'meals_count': row.meals_count,
            'items_count': items_count,
            'total_kcal': total_kcal,
            'total_carbs_g': total_carbs,
            'total_protein_g': total_protein,
            'total_fat_g': total_fat,
            'total_fiber_g': float(row.total_fiber_g),
            'total_sodium_mg': int(row.total_sodium_mg),
            'pct_kcal_carbs': pct_carbs,
            'pct_kcal_protein': pct_protein,
            'pct_kcal_fat': pct_fat,
        }

    async def _load_items(self, consumption_id: int) -> list[dict]:
        """Load consumption items."""
        q = select(ConsumptionItems).where(
            ConsumptionItems.consumption_id == consumption_id
        )
        q = q.order_by(ConsumptionItems.position)
        r = await self.s.execute(q)
        items = r.scalars().all()
        return [
            {
                "id": item.id,
                "food_id": item.food_id,
                "custom_food_id": item.custom_food_id,
                "original_name": item.original_name,
                "quantity": float(item.quantity or 0),
                "unit": item.unit.value if item.unit else "",
                "portion_id": item.portion_id,
                "original_portion_label": item.original_portion_label,
                "grams": float(item.grams) if item.grams else None,
                "ml": float(item.ml) if item.ml else None,
                "kcal": item.kcal,
                "carbs_g": float(item.carbs_g),
                "protein_g": float(item.protein_g),
                "fat_g": float(item.fat_g),
                "fiber_g": float(item.fiber_g),
                "sodium_mg": int(item.sodium_mg),
            }
            for item in items
        ]

    async def update(self, consumption: Consumption) -> None:
        values = _consumption_to_values(consumption)
        values["updated_at"] = func.now()
        await self.s.execute(
            update(UserConsumptions)
            .where(UserConsumptions.id == consumption.id)
            .values(**values)
        )

    async def delete(self, consumption_id: int) -> None:
        await self.s.execute(
            delete(UserConsumptions).where(UserConsumptions.id == consumption_id)
        )


class SQLConsumptionItemRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, item: ConsumptionItem) -> ConsumptionItem:
        m = ConsumptionItems(**_consumption_item_to_values(item))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        item.id = m.id
        item.created_at = m.created_at
        return item

    async def get_by_consumption(self, consumption_id: int) -> list[ConsumptionItem]:
        q = select(ConsumptionItems).where(
            ConsumptionItems.consumption_id == consumption_id
        )
        q = q.order_by(ConsumptionItems.position)
        r = await self.s.execute(q)
        models = r.scalars().all()
        return [_consumption_item_from_model(m) for m in models]

    async def delete_by_consumption(self, consumption_id: int) -> None:
        await self.s.execute(
            delete(ConsumptionItems).where(
                ConsumptionItems.consumption_id == consumption_id
            )
        )

    async def delete(self, item_id: int) -> None:
        await self.s.execute(delete(ConsumptionItems).where(ConsumptionItems.id == item_id))


class SQLDailySummaryRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def upsert(self, user_id: int, target_date: date, totals: dict) -> None:
        """Insert or update a daily summary using PostgreSQL upsert.
        
        This is optimized to use a single query for both insert and update.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        
        stmt = pg_insert(DailySummaries).values(
            user_id=user_id,
            local_date=target_date,
            meals_count=totals['meals_count'],
            items_count=totals['items_count'],
            total_kcal=totals['total_kcal'],
            total_carbs_g=totals['total_carbs_g'],
            total_protein_g=totals['total_protein_g'],
            total_fat_g=totals['total_fat_g'],
            total_fiber_g=totals['total_fiber_g'],
            total_sodium_mg=totals['total_sodium_mg'],
            pct_kcal_carbs=totals.get('pct_kcal_carbs'),
            pct_kcal_protein=totals.get('pct_kcal_protein'),
            pct_kcal_fat=totals.get('pct_kcal_fat'),
            updated_at=func.now(),
        ).on_conflict_do_update(
            index_elements=['user_id', 'local_date'],
            set_={
                'meals_count': totals['meals_count'],
                'items_count': totals['items_count'],
                'total_kcal': totals['total_kcal'],
                'total_carbs_g': totals['total_carbs_g'],
                'total_protein_g': totals['total_protein_g'],
                'total_fat_g': totals['total_fat_g'],
                'total_fiber_g': totals['total_fiber_g'],
                'total_sodium_mg': totals['total_sodium_mg'],
                'pct_kcal_carbs': totals.get('pct_kcal_carbs'),
                'pct_kcal_protein': totals.get('pct_kcal_protein'),
                'pct_kcal_fat': totals.get('pct_kcal_fat'),
                'updated_at': func.now(),
            }
        )
        await self.s.execute(stmt)

    async def delete_if_empty(self, user_id: int, target_date: date) -> None:
        """Delete a daily summary if it exists."""
        await self.s.execute(
            delete(DailySummaries).where(
                and_(
                    DailySummaries.user_id == user_id,
                    DailySummaries.local_date == target_date,
                )
            )
        )

    async def get_by_user_and_date(
        self, user_id: int, target_date: date
    ) -> dict | None:
        q = select(DailySummaries).where(
            and_(
                DailySummaries.user_id == user_id,
                DailySummaries.local_date == target_date,
            )
        )
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        if not m:
            return None
        return {
            "id": str(m.id),
            "user_id": m.user_id,
            "local_date": m.local_date.isoformat(),
            "meals_count": m.meals_count,
            "items_count": m.items_count,
            "total_kcal": m.total_kcal,
            "total_carbs_g": float(m.total_carbs_g),
            "total_protein_g": float(m.total_protein_g),
            "total_fat_g": float(m.total_fat_g),
            "total_fiber_g": float(m.total_fiber_g),
            "total_sodium_mg": int(m.total_sodium_mg),
            "pct_kcal_carbs": float(m.pct_kcal_carbs) if m.pct_kcal_carbs else None,
            "pct_kcal_protein": (
                float(m.pct_kcal_protein) if m.pct_kcal_protein else None
            ),
            "pct_kcal_fat": float(m.pct_kcal_fat) if m.pct_kcal_fat else None,
            "updated_at": m.updated_at.isoformat(),
        }

    async def get_by_user_date_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        q = (
            select(DailySummaries)
            .where(
                and_(
                    DailySummaries.user_id == user_id,
                    DailySummaries.local_date >= start_date,
                    DailySummaries.local_date <= end_date,
                )
            )
            .order_by(DailySummaries.local_date.desc())
        )
        r = await self.s.execute(q)
        models = r.scalars().all()
        return [
            {
                "id": str(m.id),
                "user_id": m.user_id,
                "local_date": m.local_date.isoformat(),
                "meals_count": m.meals_count,
                "items_count": m.items_count,
                "total_kcal": m.total_kcal,
                "total_carbs_g": float(m.total_carbs_g),
                "total_protein_g": float(m.total_protein_g),
                "total_fat_g": float(m.total_fat_g),
                "total_fiber_g": float(m.total_fiber_g),
                "total_sodium_mg": int(m.total_sodium_mg),
                "pct_kcal_carbs": float(m.pct_kcal_carbs) if m.pct_kcal_carbs else None,
                "pct_kcal_protein": (
                    float(m.pct_kcal_protein) if m.pct_kcal_protein else None
                ),
                "pct_kcal_fat": float(m.pct_kcal_fat) if m.pct_kcal_fat else None,
                "updated_at": m.updated_at.isoformat(),
            }
            for m in models
        ]